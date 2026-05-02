"""
Real-time Notifications Setup
Add this to your app.py
"""

# ── Step 1: Add these imports at top of app.py ──────────────────────────────
# from flask_socketio import SocketIO, emit, join_room
# socketio = SocketIO(app, cors_allowed_origins='*')

# ── Step 2: Add SocketIO events ──────────────────────────────────────────────

# @socketio.on('connect')
# def on_connect():
#     if current_user.is_authenticated:
#         join_room(f'user_{current_user.id}')
#         join_room(f'role_{current_user.role}')

# ── Step 3: Replace your create_notice route with this ──────────────────────

NOTICE_ROUTE = '''
@app.route('/teacher/notices', methods=['GET', 'POST'])
@login_required
@teacher_required
def teacher_notices():
    if request.method == 'POST':
        n = Notice(
            title=request.form['title'],
            content=request.form['content'],
            category=request.form.get('category', 'General'),
            posted_by=current_user.name,
            date=datetime.now()
        )
        db.session.add(n)
        db.session.commit()

        # Send real-time notification to ALL students
        socketio.emit('new_notification', {
            'title': n.title,
            'message': n.content[:100] + ('...' if len(n.content) > 100 else ''),
            'category': n.category,
            'poster': current_user.name,
            'time': datetime.now().strftime('%I:%M %p'),
            'type': 'notice'
        }, room='role_student')

        # Also send to all users
        socketio.emit('new_notification', {
            'title': n.title,
            'message': n.content[:100],
            'category': n.category,
            'poster': current_user.name,
            'time': datetime.now().strftime('%I:%M %p'),
            'type': 'notice'
        }, room='role_teacher')

        flash('Notice posted and students notified!', 'success')
        return redirect(url_for('notices'))
    return render_template('teacher/post_notice.html')
'''

# ── Step 4: Add assignment notification ──────────────────────────────────────

ASSIGNMENT_ROUTE = '''
@app.route('/teacher/assignments', methods=['GET', 'POST'])
@login_required
@teacher_required
def teacher_assignments():
    students = Student.query.all()
    if request.method == 'POST':
        sids     = request.form.getlist('student_ids')
        due_date = request.form.get('due_date')
        title    = request.form['title']
        subject  = request.form['subject']

        for sid in sids:
            a = Assignment(
                student_id=int(sid),
                title=title,
                subject=subject,
                due_date=datetime.strptime(due_date, '%Y-%m-%d') if due_date else datetime.now() + timedelta(days=7),
                status='Pending'
            )
            db.session.add(a)

            # Get student user_id for targeted notification
            s = Student.query.get(int(sid))
            if s:
                # Send real-time notification to specific student
                socketio.emit('new_notification', {
                    'title': f'New Assignment: {title}',
                    'message': f'Subject: {subject} | Due: {due_date}',
                    'category': 'Assignment',
                    'poster': current_user.name,
                    'time': datetime.now().strftime('%I:%M %p'),
                    'type': 'assignment'
                }, room=f'user_{s.user_id}')

        db.session.commit()
        flash(f'Assignment assigned to {len(sids)} students!', 'success')
        return redirect(url_for('teacher_assignments'))

    all_assignments = Assignment.query.order_by(Assignment.due_date.desc()).limit(30).all()
    now = datetime.now()
    return render_template('teacher/assignments.html',
        students=students, assignments=all_assignments, now=now)
'''