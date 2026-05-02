from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from models import db
from models.user import User
from models.student import Student, Attendance, Result, Fee, Assignment
from models.notice import Notice, Event
from models.library import Book, BorrowRecord
from datetime import datetime, date, timedelta
from functools import wraps
import secrets
from flask import session, abort
# Optional Flask-WTF integration (initialized after app is created)
USE_WTF = False

app = Flask(__name__)
app.config.from_object(Config)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please login to continue.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Optional Flask-WTF integration (import and init after app exists)
USE_WTF = False
try:
    from flask_wtf import FlaskForm, CSRFProtect
    from wtforms import SubmitField
    USE_WTF = True
except Exception:
    USE_WTF = False

if USE_WTF:
    csrf = CSRFProtect()
    # ensure SECRET_KEY exists (Config should supply it, but fallback)
    if not app.config.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = secrets.token_urlsafe(32)
    csrf.init_app(app)

if USE_WTF:
    class FeeMarkForm(FlaskForm):
        submit = SubmitField('Mark Paid')
else:
    FeeMarkForm = None


# --- CSRF helpers (simple token stored in session) ------------------------
def _get_csrf_token():
    t = session.get('_csrf_token')
    if not t:
        t = secrets.token_urlsafe(16)
        session['_csrf_token'] = t
    return t


@app.context_processor
def inject_csrf_token():
    # provides `csrf_token` in templates
    return dict(csrf_token=_get_csrf_token())


if USE_WTF:
    class FeeMarkForm(FlaskForm):
        submit = SubmitField('Mark Paid')
else:
    FeeMarkForm = None


def verify_csrf():
    token = session.get('_csrf_token')
    form_token = request.form.get('_csrf_token') or request.headers.get('X-CSRF-Token')
    if not token or not form_token or token != form_token:
        abort(400, 'CSRF token missing or invalid')

# ── Import API Blueprints ────────────────────────────────────────────────────
try:
    from api.student import student_bp
    from api.teacher import teacher_bp
    from api.api_admin import admin_bp
    app.register_blueprint(student_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(admin_bp)
    print("✅ API Blueprints registered successfully")
except ImportError as e:
    print(f"⚠️  Warning: Could not import API blueprints: {e}")

# ── Role Decorators ──────────────────────────────────────────────────────────
def admin_required(f):
    @wraps(f)
    def dec(*a, **kw):
        if current_user.role != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*a, **kw)
    return dec

def teacher_required(f):
    @wraps(f)
    def dec(*a, **kw):
        if current_user.role not in ('admin', 'teacher'):
            flash('Teacher access required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*a, **kw)
    return dec

# ══════════════════════════════════════════════════════════════════════════════
# HOME
# ══════════════════════════════════════════════════════════════════════════════
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# ══════════════════════════════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════════════════════════════
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        user     = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=bool(request.form.get('remember')))
            flash(f'Welcome back, {user.name.split()[0]}!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid email or password.', 'danger')
    return render_template('auth/login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        role     = request.form.get('role', 'student')

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('auth/register.html')

        user = User(name=name, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        if role == 'student':
            roll_no  = request.form.get('roll_no', '')
            branch   = request.form.get('branch', '')
            semester = request.form.get('semester', '1')
            student  = Student(
                user_id=user.id,
                roll_no=roll_no,
                branch=branch,
                semester=int(semester) if semester else 1
            )
            db.session.add(student)

        db.session.commit()
        flash('Account created! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('auth/register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD — role-based redirect
# ══════════════════════════════════════════════════════════════════════════════
@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin'))
    if current_user.role == 'teacher':
        return redirect(url_for('teacher_dashboard'))

    # ── Student Dashboard ────────────────────────────────────────────────────
    student = Student.query.filter_by(user_id=current_user.id).first()
    notices = Notice.query.order_by(Notice.created_at.desc()).limit(4).all()
    events  = Event.query.order_by(Event.event_date).limit(4).all()

    att_pct = present = total_att = 0
    fees_due = 0
    results  = []

    if student:
        all_att   = Attendance.query.filter_by(student_id=student.id).all()
        total_att = len(all_att)
        present   = sum(1 for a in all_att if a.status in ('Present', 'present'))
        att_pct   = round(present / total_att * 100, 1) if total_att else 0
        fees_due  = Fee.query.filter_by(student_id=student.id, status='Pending').count()
        results   = Result.query.filter_by(student_id=student.id).order_by(Result.id.desc()).limit(5).all()

    return render_template('student/dashboard.html',
        student=student, notices=notices, events=events,
        att_pct=att_pct, present=present, total_att=total_att,
        fees_due=fees_due, results=results)

# ══════════════════════════════════════════════════════════════════════════════
# STUDENT ROUTES
# ══════════════════════════════════════════════════════════════════════════════
@app.route('/profile')
@login_required
def profile():
    student = Student.query.filter_by(user_id=current_user.id).first()
    return render_template('student/profile.html', student=student)


@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    student = Student.query.filter_by(user_id=current_user.id).first()
    if request.method == 'POST':
        current_user.name = request.form.get('name', current_user.name)
        if student:
            student.phone       = request.form.get('phone', '')
            student.branch      = request.form.get('branch', student.branch)
            student.blood_group = request.form.get('blood_group', '')
            student.father_name = request.form.get('father_name', '')
            student.address     = request.form.get('address', '')
            student.bio         = request.form.get('bio', '')
        db.session.commit()
        flash('Profile updated!', 'success')
        return redirect(url_for('profile'))
    return render_template('student/edit_profile.html', student=student)


@app.route('/attendance')
@login_required
def attendance():
    student = Student.query.filter_by(user_id=current_user.id).first()
    records = []
    summary = {}
    if student:
        records  = Attendance.query.filter_by(student_id=student.id).order_by(Attendance.date.desc()).all()
        subjects = list(set(r.subject for r in records))
        for subj in subjects:
            sr      = [r for r in records if r.subject == subj]
            present = sum(1 for r in sr if r.status in ('Present','present'))
            summary[subj] = {
                'total': len(sr), 'present': present,
                'pct': round(present / len(sr) * 100, 1) if sr else 0
            }
    return render_template('student/attendance.html', student=student, records=records, summary=summary)


@app.route('/results')
@login_required
def results():
    student     = Student.query.filter_by(user_id=current_user.id).first()
    all_results = Result.query.filter_by(student_id=student.id).all() if student else []
    sgpa = 0
    if all_results:
        sgpa = round(sum(r.internal + r.external for r in all_results) / len(all_results) / 10, 2)
    return render_template('student/results.html', student=student, results=all_results, sgpa=sgpa)


@app.route('/notices')
@login_required
def notices():
    category = request.args.get('category', 'all')
    q = Notice.query.order_by(Notice.created_at.desc())
    if category != 'all':
        q = q.filter_by(category=category)
    return render_template('student/notices.html', notices=q.all(), category=category)


@app.route('/notices/create', methods=['GET', 'POST'])
@login_required
@teacher_required
def create_notice():
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
        flash('Notice posted!', 'success')
        return redirect(url_for('notices'))
    return render_template('student/create_notice.html')


@app.route('/library')
@login_required
def library():
    search  = request.args.get('q', '')
    student = Student.query.filter_by(user_id=current_user.id).first()
    books   = Book.query.filter(Book.title.ilike(f'%{search}%')).all() if search else Book.query.all()
    borrowed = BorrowRecord.query.filter_by(
        student_id=student.id if student else 0, status='Active').all()
    return render_template('student/library.html', books=books, borrowed=borrowed, search=search)


@app.route('/library/borrow/<int:bid>', methods=['POST'])
@login_required
def borrow_book(bid):
    book    = Book.query.get_or_404(bid)
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        flash('Student profile not found.', 'danger')
        return redirect(url_for('library'))
    if book.available_copies < 1:
        flash('No copies available.', 'danger')
        return redirect(url_for('library'))
    rec = BorrowRecord(book_id=bid, student_id=student.id,
                       borrow_date=date.today(),
                       due_date=date.today() + timedelta(days=14), status='Active')
    book.available_copies -= 1
    db.session.add(rec)
    db.session.commit()
    flash(f'"{book.title}" issued for 14 days!', 'success')
    return redirect(url_for('library'))


@app.route('/library/return/<int:rid>', methods=['POST'])
@login_required
def return_book(rid):
    rec  = BorrowRecord.query.get_or_404(rid)
    rec.return_date = date.today()
    rec.status      = 'Returned'
    rec.book.available_copies += 1
    db.session.commit()
    flash('Book returned successfully!', 'success')
    return redirect(url_for('library'))


@app.route('/events')
@login_required
def events():
    upcoming = Event.query.filter(Event.event_date >= date.today()).order_by(Event.event_date).all()
    past     = Event.query.filter(Event.event_date < date.today()).order_by(Event.event_date.desc()).limit(4).all()
    return render_template('student/events.html', upcoming=upcoming, past=past)


@app.route('/timetable')
@login_required
def timetable():
    student = Student.query.filter_by(user_id=current_user.id).first()
    return render_template('student/timetable.html', student=student)


@app.route('/assignments')
@login_required
def assignments():
    student     = Student.query.filter_by(user_id=current_user.id).first()
    assignments = Assignment.query.filter_by(
        student_id=student.id if student else 0).order_by(Assignment.due_date).all()
    return render_template('student/assignments.html', assignments=assignments)


@app.route('/assignments/submit/<int:aid>', methods=['POST'])
@login_required
def submit_assignment(aid):
    a = Assignment.query.get_or_404(aid)
    a.status = 'Submitted'
    db.session.commit()
    flash('Assignment submitted!', 'success')
    return redirect(url_for('assignments'))


@app.route('/fees')
@login_required
def fees():
    student  = Student.query.filter_by(user_id=current_user.id).first()
    all_fees = Fee.query.filter_by(student_id=student.id if student else 0).all()
    total_paid = sum(f.amount for f in all_fees if f.status == 'Paid')
    total_due  = sum(f.amount for f in all_fees if f.status == 'Pending')
    return render_template('student/fees.html', fees=all_fees, student=student,
                           total_paid=total_paid, total_due=total_due)


@app.route('/fees/pay/<int:fid>', methods=['POST'])
@login_required
def pay_fee(fid):
    fee = Fee.query.get_or_404(fid)
    fee.status  = 'Paid'
    fee.paid_on = datetime.now()
    db.session.commit()
    flash('Payment successful!', 'success')
    return redirect(url_for('fees'))

# ══════════════════════════════════════════════════════════════════════════════
# TEACHER ROUTES
# ══════════════════════════════════════════════════════════════════════════════
@app.route('/teacher/dashboard')
@login_required
def teacher_dashboard():
    if current_user.role != 'teacher':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    return render_template('teacher/dashboard.html')
    


@app.route('/teacher/students')
@login_required
@teacher_required
def teacher_students():
    branch   = request.args.get('branch', '')
    semester = request.args.get('semester', '')
    q = Student.query
    if branch:   q = q.filter_by(branch=branch)
    if semester: q = q.filter_by(semester=int(semester))
    students = q.all()
    return render_template('teacher/students.html', students=students, branch=branch, semester=semester)


@app.route('/teacher/attendance', methods=['GET', 'POST'])
@login_required
@teacher_required
def teacher_attendance():
    students = Student.query.all()
    if request.method == 'POST':
        subject  = request.form.get('subject')
        att_date = request.form.get('att_date')
        att_date = date.fromisoformat(att_date) if att_date else date.today()
        for sid in request.form.getlist('student_ids'):
            status   = request.form.get(f'status_{sid}', 'Present')
            existing = Attendance.query.filter_by(
                student_id=int(sid), subject=subject, date=att_date).first()
            if existing:
                existing.status = status
            else:
                db.session.add(Attendance(
                    student_id=int(sid), subject=subject,
                    date=att_date, status=status))
        db.session.commit()
        flash(f'Attendance marked for {subject} on {att_date}!', 'success')
        return redirect(url_for('teacher_attendance'))
    return render_template('teacher/mark_attendance.html', students=students)


@app.route('/teacher/results', methods=['GET', 'POST'])
@login_required
@teacher_required
def teacher_results():
    students = Student.query.all()
    if request.method == 'POST':
        r = Result(
            student_id=int(request.form['student_id']),
            subject=request.form['subject'],
            semester=int(request.form.get('semester', 1)),
            internal=float(request.form.get('internal', 0)),
            external=float(request.form.get('external', 0)),
            grade=request.form.get('grade', '')
        )
        db.session.add(r)
        db.session.commit()
        flash('Result added!', 'success')
        return redirect(url_for('teacher_results'))
    return render_template('teacher/add_result.html', students=students)


@app.route('/teacher/assignments', methods=['GET', 'POST'])
@login_required
@teacher_required
def teacher_assignments():
    students = Student.query.all()
    if request.method == 'POST':
        sids     = request.form.getlist('student_ids')
        due_date = request.form.get('due_date')
        for sid in sids:
            a = Assignment(
                student_id=int(sid),
                title=request.form['title'],
                subject=request.form['subject'],
                due_date=datetime.strptime(due_date, '%Y-%m-%d') if due_date else datetime.now() + timedelta(days=7),
                status='Pending'
            )
            db.session.add(a)
        db.session.commit()
        flash(f'Assignment assigned to {len(sids)} students!', 'success')
        return redirect(url_for('teacher_assignments'))
    all_assignments = Assignment.query.order_by(Assignment.due_date.desc()).limit(20).all()
    return render_template('teacher/assignments.html', students=students, assignments=all_assignments)


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
        flash('Notice posted!', 'success')
        return redirect(url_for('notices'))
    return render_template('teacher/post_notice.html')

# ══════════════════════════════════════════════════════════════════════════════
# ADMIN ROUTES
# ══════════════════════════════════════════════════════════════════════════════
@app.route('/admin')
@login_required
@admin_required
def admin():
    total_students = User.query.filter_by(role='student').count()
    total_teachers = User.query.filter_by(role='teacher').count()
    total_books    = Book.query.count()
    total_notices  = Notice.query.count()
    pending_fees   = Fee.query.filter_by(status='Pending').count()
    recent_users   = User.query.order_by(User.created_at.desc()).limit(10).all()
    # Also provide a list of recent student objects for the dashboard template
    recent_students = Student.query.order_by(Student.id.desc()).limit(10).all()
    # Additional detailed admin data with pagination and sorting
    # Fees list
    fees_page = int(request.args.get('fees_page', 1))
    fees_per = int(request.args.get('fees_per', 10))
    fees_sort = request.args.get('fees_sort', 'id_desc')
    q_pending = Fee.query.filter_by(status='Pending')
    if fees_sort == 'amount_asc':
        q_pending = q_pending.order_by(Fee.amount.asc())
    elif fees_sort == 'amount_desc':
        q_pending = q_pending.order_by(Fee.amount.desc())
    else:
        q_pending = q_pending.order_by(Fee.id.desc())
    pending_fees_count = q_pending.count()
    pending_fees_list = q_pending.offset((fees_page-1)*fees_per).limit(fees_per).all()

    # Recent payments (paid)
    payments_page = int(request.args.get('payments_page', 1))
    payments_per = int(request.args.get('payments_per', 10))
    payments_sort = request.args.get('payments_sort', 'id_desc')
    q_paid = Fee.query.filter_by(status='Paid')
    if payments_sort == 'amount_asc':
        q_paid = q_paid.order_by(Fee.amount.asc())
    elif payments_sort == 'amount_desc':
        q_paid = q_paid.order_by(Fee.amount.desc())
    else:
        q_paid = q_paid.order_by(Fee.id.desc())
    recent_payments_count = q_paid.count()
    recent_payments = q_paid.offset((payments_page-1)*payments_per).limit(payments_per).all()

    # Teachers summary: name, email, notices posted
    teachers = User.query.filter_by(role='teacher').order_by(User.name).all()
    teacher_summaries = []
    for t in teachers:
        notices_by_t = Notice.query.filter_by(posted_by=t.name).count()
        teacher_summaries.append({'name': t.name, 'email': t.email, 'notices': notices_by_t})

    # Attendance issues: students with attendance pct below threshold (75%)
    attendance_issues = []
    ATT_THRESHOLD = 75.0
    all_students = Student.query.all()
    for s in all_students:
        all_att = Attendance.query.filter_by(student_id=s.id).all()
        total_att_s = len(all_att)
        if total_att_s == 0:
            continue
        present_s = sum(1 for a in all_att if a.status in ('Present', 'present'))
        pct = round(present_s / total_att_s * 100, 1)
        if pct < ATT_THRESHOLD:
            # try to get user name
            uname = s.user.name if getattr(s, 'user', None) else 'Unknown'
            attendance_issues.append({'student': uname, 'present': present_s, 'total': total_att_s, 'pct': pct})
    return render_template('admin/dashboard.html',
        total_students=total_students, total_teachers=total_teachers,
        total_books=total_books, total_notices=total_notices,
        pending_fees=pending_fees, recent_users=recent_users,
        students=recent_students,
        pending_fees_list=pending_fees_list, recent_payments=recent_payments,
        teacher_summaries=teacher_summaries, attendance_issues=attendance_issues,
        pending_fees_count=pending_fees_count, fees_page=fees_page, fees_per=fees_per,
        recent_payments_count=recent_payments_count, payments_page=payments_page, payments_per=payments_per)


@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    if request.method == 'POST':
        # handle promote/change role from template form
        promote_id = request.form.get('promote_id')
        new_role = request.form.get('new_role')
        if promote_id and new_role:
            u = User.query.get(int(promote_id))
            if u:
                u.role = new_role
                db.session.commit()
                flash('User role updated.', 'success')
            return redirect(url_for('admin_users'))

    role  = request.args.get('role', 'all')
    q     = User.query if role == 'all' else User.query.filter_by(role=role)
    users = q.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users, role=role)


@app.route('/admin/users/delete/<int:uid>', methods=['POST'])
@login_required
@admin_required
def delete_user(uid):
    user = User.query.get_or_404(uid)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted.', 'success')
    return redirect(url_for('admin_users'))


@app.route('/admin/fees')
@login_required
@admin_required
def admin_fees():
    all_fees = Fee.query.order_by(Fee.student_id).all()
    return render_template('admin/fees.html', fees=all_fees)


@app.route('/admin/fees/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_fee():
    students = Student.query.all()
    if request.method == 'POST':
        f = Fee(
            student_id=int(request.form['student_id']),
            description=request.form['description'],
            amount=float(request.form['amount']),
            status='Pending'
        )
        db.session.add(f)
        db.session.commit()
        flash('Fee added!', 'success')
        return redirect(url_for('admin_fees'))
    return render_template('admin/add_fee.html', students=students)


@app.route('/admin/books', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_books():
    if request.method == 'POST':
        b = Book(
            title=request.form['title'],
            author=request.form.get('author', ''),
            isbn=request.form.get('isbn', ''),
            category=request.form.get('category', ''),
            total_copies=int(request.form.get('copies', 1)),
            available_copies=int(request.form.get('copies', 1))
        )
        db.session.add(b)
        db.session.commit()
        flash('Book added!', 'success')
        return redirect(url_for('library'))
    return render_template('admin/add_book.html')


@app.route('/admin/fees/mark_paid/<int:fid>', methods=['POST'])
@login_required
@admin_required
def admin_mark_fee_paid(fid):
    verify_csrf()
    fee = Fee.query.get_or_404(fid)
    fee.status = 'Paid'
    fee.paid_on = datetime.now()
    db.session.commit()
    flash('Fee marked as paid.', 'success')
    return redirect(request.referrer or url_for('admin_fees'))


@app.route('/admin/fees/<int:fid>')
@login_required
@admin_required
def admin_fee_detail(fid):
    fee = Fee.query.get_or_404(fid)
    student = Student.query.filter_by(id=fee.student_id).first()
    return render_template('admin/fee_detail.html', fee=fee, student=student)


@app.route('/admin/student/<int:sid>')
@login_required
@admin_required
def admin_student_profile(sid):
    student = Student.query.get_or_404(sid)
    user = User.query.get(student.user_id) if student.user_id else None
    fees = Fee.query.filter_by(student_id=student.id).all()
    attendance = Attendance.query.filter_by(student_id=student.id).order_by(Attendance.date.desc()).all()
    results = Result.query.filter_by(student_id=student.id).order_by(Result.id.desc()).all()
    return render_template('admin/student_profile.html', student=student, user=user, fees=fees, attendance=attendance, results=results)

# ══════════════════════════════════════════════════════════════════════════════
# SEED DATA
# ══════════════════════════════════════════════════════════════════════════════
@app.route('/seed')
def seed():
    db.create_all()

    if not User.query.filter_by(email='admin@campus.edu').first():
        a = User(name='Admin User', email='admin@campus.edu', role='admin')
        a.set_password('admin123')
        db.session.add(a)

    if not User.query.filter_by(email='teacher@campus.edu').first():
        t = User(name='Dr. Priya Sharma', email='teacher@campus.edu', role='teacher')
        t.set_password('teacher123')
        db.session.add(t)

    if not User.query.filter_by(email='student@campus.edu').first():
        u = User(name='Dristy Pal', email='student@campus.edu', role='student')
        u.set_password('student123')
        db.session.add(u)
        db.session.flush()
        s = Student(user_id=u.id, roll_no='CS21B001', branch='B.Tech CSE',
                    semester=5, cgpa=8.5, phone='9876543210')
        db.session.add(s)
        db.session.flush()

        for subj, i, e, g in [
            ('Data Structures', 35, 65, 'A'),
            ('Database Systems', 37, 67, 'A+'),
            ('Web Development', 39, 67, 'A'),
            ('Machine Learning', 41, 68, 'A+'),
            ('Algorithms', 43, 69, 'A')
        ]:
            db.session.add(Result(student_id=s.id, subject=subj, semester=5, internal=i, external=e, grade=g))

        for desc, amt, status in [
            ('Semester 5 Tuition Fee', 45000, 'Paid'),
            ('Hostel Fee', 25000, 'Paid'),
            ('Exam Fee', 5000, 'Pending'),
            ('Library Fee', 1000, 'Pending')
        ]:
            db.session.add(Fee(student_id=s.id, description=desc, amount=amt, status=status))

        for title, subj in [
            ('Tree Traversal Problems', 'Data Structures'),
            ('Database Design Project', 'Database Systems'),
            ('Django REST API', 'Web Development')
        ]:
            db.session.add(Assignment(student_id=s.id, title=title, subject=subj,
                due_date=datetime.now() + timedelta(days=10), status='Pending'))

        for subj in ['Data Structures', 'Database Systems', 'Web Development', 'Machine Learning', 'Algorithms']:
            for day in range(20):
                db.session.add(Attendance(student_id=s.id, subject=subj,
                    date=date.today() - timedelta(days=day),
                    status='Present' if day % 4 != 0 else 'Absent'))

    for title, cat, by, content in [
        ('Mid-Sem Exam Schedule Released', 'Exams', 'Exam Cell',
         'Mid-semester examinations will commence from May 10th. Students must collect hall tickets from their department office one week prior.'),
        ('Campus Placement Drive — TCS & Infosys', 'Placement', 'Placement Cell',
         'TCS and Infosys will conduct campus placement on May 5th. All eligible final year students must register before April 30th.'),
        ('Summer Vacation 2025', 'Holiday', 'Admin',
         'College will remain closed for summer vacation from May 20th to June 15th.'),
        ('Annual Cultural Fest — VIBE 2025', 'General', 'Student Council',
         'VIBE 2025 is scheduled for May 15–17. Register for dance, music, drama and art competitions!'),
        ('Library Fine Waiver Scheme', 'General', 'Library Dept',
         'One-time fine waiver for all overdue books if returned before May 1st.')
    ]:
        if not Notice.query.filter_by(title=title).first():
            db.session.add(Notice(title=title, category=cat, posted_by=by,
                                  content=content, date=datetime.now()))

    for title, cat, d, desc in [
        ('Hackathon 2025', 'Technical', date(2026, 5, 15), 'Annual coding hackathon. Build innovative solutions in 24 hours!'),
        ('AI/ML Tech Talk', 'Seminar', date(2026, 5, 8), 'Expert talk on latest AI trends and career opportunities.'),
        ('Annual Sports Week', 'Sports', date(2026, 5, 20), 'Cricket, football, badminton and athletics competitions.'),
        ('Cultural Fest Nexus', 'Cultural', date(2026, 6, 1), 'Dance, music and drama. Come celebrate campus culture!')
    ]:
        if not Event.query.filter_by(title=title).first():
            db.session.add(Event(title=title, category=cat, event_date=d, description=desc))

    for title, author, cat, copies in [
        ('Introduction to Algorithms', 'Cormen', 'Computer Science', 3),
        ('Clean Code', 'Robert Martin', 'Software Engineering', 2),
        ('Operating Systems', 'Silberschatz', 'Computer Science', 4),
        ('Design Patterns', 'GoF', 'Software Engineering', 2),
        ('Computer Networks', 'Tanenbaum', 'Computer Science', 3),
        ('Database System Concepts', 'Korth', 'Computer Science', 3),
        ('Python Crash Course', 'Eric Matthes', 'Programming', 5)
    ]:
        if not Book.query.filter_by(title=title).first():
            db.session.add(Book(title=title, author=author, isbn='ISBN-' + title[:5],
                                category=cat, total_copies=copies, available_copies=copies - 1))

    # Add several sample students (idempotent) so lists like assignments/attendance show
    sample_students = [
        ('Alice Johnson', 'alice@campus.edu', 'CS21B002', 'B.Tech CSE', 5),
        ('Bob Kumar', 'bob@campus.edu', 'CS21B003', 'B.Tech ECE', 4),
        ('Carol Singh', 'carol@campus.edu', 'CS21B004', 'B.Tech ME', 6),
    ]
    for name, email, roll, branch, sem in sample_students:
        if not User.query.filter_by(email=email).first():
            u = User(name=name, email=email, role='student')
            u.set_password('student123')
            db.session.add(u)
            db.session.flush()
            s = Student(user_id=u.id, roll_no=roll, branch=branch, semester=sem, cgpa=7.5)
            db.session.add(s)
            # add a pending fee
            db.session.add(Fee(student_id=s.id, description='Library Fine', amount=200.0, status='Pending'))
            # add one assignment
            db.session.add(Assignment(student_id=s.id, title='Intro Project', subject='Web Development', due_date=datetime.now()+timedelta(days=7), status='Pending'))
            # add some attendance records
            for day in range(5):
                db.session.add(Attendance(student_id=s.id, subject='Web Development', date=date.today()-timedelta(days=day), status='Present' if day % 4 != 0 else 'Absent'))
            # add a result
            db.session.add(Result(student_id=s.id, subject='Data Structures', semester=sem, internal=30+day%5, external=50+day%5, grade='B'))

    # Ensure there are a few more notices and events for the UI
    extra_notices = [
        ('Guest Lecture: Cloud Computing', 'Seminar', 'CS Dept', 'Join the guest lecture on cloud native apps this Friday.'),
        ('Scholarship Info Session', 'Placement', 'Placement Cell', 'Information session about new scholarships for meritorious students.'),
    ]
    for title, cat, by, content in extra_notices:
        if not Notice.query.filter_by(title=title).first():
            db.session.add(Notice(title=title, category=cat, posted_by=by, content=content, date=datetime.now()))

    extra_events = [
        ('Tech Talk: REST APIs', 'Technical', date.today() + timedelta(days=3), 'A technical talk on designing robust REST APIs.'),
        ('Sports Meet', 'Sports', date.today() + timedelta(days=10), 'Inter-college sports meet.'),
    ]
    for title, cat, d, desc in extra_events:
        if not Event.query.filter_by(title=title).first():
            db.session.add(Event(title=title, category=cat, event_date=d, description=desc))

    db.session.commit()
    return '''
    <div style="font-family:'Outfit',sans-serif;background:#0a0f1e;color:#fff;min-height:100vh;padding:50px;">
        <h1 style="color:#38bdf8;font-size:28px;">✅ Campus Connect - Seeded!</h1><br/>
        <p style="color:rgba(255,255,255,0.6);margin-bottom:24px;">Use these accounts to login:</p>
        <table style="font-size:15px;border-collapse:collapse;background:rgba(255,255,255,0.05);border-radius:12px;overflow:hidden;">
            <tr style="background:rgba(56,189,248,0.15);color:#38bdf8;">
                <td style="padding:12px 30px;">Role</td>
                <td style="padding:12px 30px;">Email</td>
                <td style="padding:12px 30px;">Password</td>
            </tr>
            <tr style="border-top:1px solid rgba(255,255,255,0.08);">
                <td style="padding:12px 30px;">🛡️ Admin</td>
                <td style="padding:12px 30px;font-family:monospace;color:#38bdf8;">admin@campus.edu</td>
                <td style="padding:12px 30px;font-family:monospace;">admin123</td>
            </tr>
            <tr style="border-top:1px solid rgba(255,255,255,0.08);">
                <td style="padding:12px 30px;">👨‍🏫 Teacher</td>
                <td style="padding:12px 30px;font-family:monospace;color:#38bdf8;">teacher@campus.edu</td>
                <td style="padding:12px 30px;font-family:monospace;">teacher123</td>
            </tr>
            <tr style="border-top:1px solid rgba(255,255,255,0.08);">
                <td style="padding:12px 30px;">🎓 Student</td>
                <td style="padding:12px 30px;font-family:monospace;color:#38bdf8;">student@campus.edu</td>
                <td style="padding:12px 30px;font-family:monospace;">student123</td>
            </tr>
        </table>
        <br/><br/>
        <a href="/login" style="background:#1a56db;color:#fff;padding:14px 32px;border-radius:10px;text-decoration:none;font-weight:700;font-size:15px;">Go to Login →</a>
    </div>'''

# ══════════════════════════════════════════════════════════════════════════════
# ERROR HANDLERS
# ══════════════════════════════════════════════════════════════════════════════
@app.errorhandler(404)
def not_found(e):
    return '''<div style="font-family:sans-serif;background:#0a0f1e;color:#fff;min-height:100vh;
    display:flex;align-items:center;justify-content:center;flex-direction:column;gap:16px;">
    <h1 style="font-size:80px;color:#38bdf8;margin:0;">404</h1>
    <p style="color:rgba(255,255,255,0.5);font-size:18px;">Page not found</p>
    <a href="/dashboard" style="background:#1a56db;color:#fff;padding:12px 28px;border-radius:10px;text-decoration:none;">Go Home</a>
    </div>''', 404

@app.errorhandler(500)
def server_error(e):
    return '''<div style="font-family:sans-serif;background:#0a0f1e;color:#fff;min-height:100vh;
    display:flex;align-items:center;justify-content:center;flex-direction:column;gap:16px;">
    <h1 style="font-size:80px;color:#E53935;margin:0;">500</h1>
    <p style="color:rgba(255,255,255,0.5);font-size:18px;">Server error. Please try again.</p>
    <a href="/dashboard" style="background:#1a56db;color:#fff;padding:12px 28px;border-radius:10px;text-decoration:none;">Go Home</a>
    </div>''', 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
@app.route('/teacher/profile')
@login_required
@teacher_required
def teacher_profile():
    total_students    = Student.query.count()
    total_assignments = Assignment.query.count()
    total_notices     = Notice.query.filter_by(posted_by=current_user.name).count()
    recent_notices    = Notice.query.filter_by(posted_by=current_user.name).order_by(Notice.date.desc()).limit(5).all()
    return render_template('teacher/profile.html',
        total_students=total_students,
        total_assignments=total_assignments,
        total_notices=total_notices,
        recent_notices=recent_notices)
