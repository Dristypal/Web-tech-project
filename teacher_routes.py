from flask import Blueprint, request, jsonify, session
from datetime import datetime
from extensions import db

teacher_bp = Blueprint('teacher', __name__, url_prefix='/api/teacher')

# ─── Helper ───────────────────────────────────────────────────────────────────
def teacher_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'teacher':
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

def get_teacher_id():
    return session.get('user_id')

# ─── Dashboard ────────────────────────────────────────────────────────────────
@teacher_bp.route('/dashboard')
@teacher_required
def dashboard():
    teacher_id = get_teacher_id()
    total_students = db.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    total_assignments = db.execute(
        "SELECT COUNT(*) FROM assignments WHERE teacher_id=?", (teacher_id,)
    ).fetchone()[0]
    pending = db.execute(
        "SELECT COUNT(*) FROM assignments WHERE teacher_id=? AND status='Pending'",
        (teacher_id,)
    ).fetchone()[0]
    att = db.execute(
        "SELECT ROUND(SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END)*100.0/COUNT(*),1) FROM attendance"
    ).fetchone()[0] or 0
    return jsonify({'status':'ok','data':{'metrics':{
        'total_students': total_students,
        'total_assignments': total_assignments,
        'pending': pending,
        'avg_attendance': att
    }}})

# ─── Profile ──────────────────────────────────────────────────────────────────
@teacher_bp.route('/profile')
@teacher_required
def profile():
    row = db.execute("SELECT id,name,email,role FROM users WHERE id=?", (get_teacher_id(),)).fetchone()
    return jsonify({'status':'ok','data':{'name':row[1],'email':row[2],'role':row[3]}})

# ─── Students ─────────────────────────────────────────────────────────────────
@teacher_bp.route('/students')
@teacher_required
def students():
    per_page = int(request.args.get('per_page', 20))
    rows = db.execute(
        "SELECT id,name,roll_no,branch,semester,cgpa FROM students LIMIT ?", (per_page,)
    ).fetchall()
    return jsonify({'status':'ok','data':{'students':[
        {'id':r[0],'name':r[1],'roll_no':r[2],'branch':r[3],'semester':r[4],'cgpa':r[5]} for r in rows
    ]}})

@teacher_bp.route('/students/<int:sid>')
@teacher_required
def student_detail(sid):
    s = db.execute("SELECT id,name,email,roll_no,branch,semester,cgpa,phone FROM students WHERE id=?", (sid,)).fetchone()
    if not s:
        return jsonify({'error':'Not found'}), 404
    total_att = db.execute("SELECT COUNT(*) FROM attendance WHERE student_id=?", (sid,)).fetchone()[0]
    present   = db.execute("SELECT COUNT(*) FROM attendance WHERE student_id=? AND status='Present'", (sid,)).fetchone()[0]
    total_res = db.execute("SELECT COUNT(*) FROM results WHERE student_id=?", (sid,)).fetchone()[0]
    total_asgn= db.execute("SELECT COUNT(*) FROM assignments WHERE student_id=?", (sid,)).fetchone()[0]
    submitted = db.execute("SELECT COUNT(*) FROM assignments WHERE student_id=? AND status='Submitted'", (sid,)).fetchone()[0]
    return jsonify({'status':'ok','data':{
        'student_info':{'id':s[0],'name':s[1],'email':s[2],'roll_no':s[3],'branch':s[4],'semester':s[5],'cgpa':s[6],'phone':s[7]},
        'stats':{'attendance': round(present*100/total_att,1) if total_att else 0,'total_att':total_att,'total_results':total_res,'total_assignments':total_asgn,'submitted':submitted}
    }})

# ─── Results ──────────────────────────────────────────────────────────────────
@teacher_bp.route('/results')
@teacher_required
def results():
    per_page = int(request.args.get('per_page', 15))
    rows = db.execute(
        "SELECT id,student_id,subject,internal,external,grade,semester FROM results LIMIT ?", (per_page,)
    ).fetchall()
    return jsonify({'status':'ok','data':{'results':[
        {'id':r[0],'student_id':r[1],'subject':r[2],'internal':r[3],'external':r[4],'grade':r[5],'semester':r[6]} for r in rows
    ]}})

@teacher_bp.route('/results/add', methods=['POST'])
@teacher_required
def add_result():
    d = request.get_json()
    required = ['student_id','subject','internal','external','grade','semester']
    if not all(k in d for k in required):
        return jsonify({'error':'Missing fields'}), 400
    db.execute(
        "INSERT INTO results (student_id,subject,internal,external,grade,semester,created_at) VALUES (?,?,?,?,?,?,?)",
        (d['student_id'],d['subject'],d['internal'],d['external'],d['grade'],d['semester'],datetime.now().isoformat())
    )
    db.commit()
    return jsonify({'status':'ok','message':'Result added successfully'})

@teacher_bp.route('/results/<int:rid>', methods=['PUT'])
@teacher_required
def edit_result(rid):
    d = request.get_json()
    db.execute(
        "UPDATE results SET subject=?,internal=?,external=?,grade=?,semester=? WHERE id=?",
        (d.get('subject'),d.get('internal'),d.get('external'),d.get('grade'),d.get('semester'),rid)
    )
    db.commit()
    return jsonify({'status':'ok','message':'Result updated'})

@teacher_bp.route('/results/<int:rid>', methods=['DELETE'])
@teacher_required
def delete_result(rid):
    db.execute("DELETE FROM results WHERE id=?", (rid,))
    db.commit()
    return jsonify({'status':'ok','message':'Result deleted'})

# ─── Attendance ───────────────────────────────────────────────────────────────
@teacher_bp.route('/attendance')
@teacher_required
def attendance():
    per_page = int(request.args.get('per_page', 20))
    rows = db.execute(
        "SELECT id,student_id,subject,date,status FROM attendance ORDER BY date DESC LIMIT ?", (per_page,)
    ).fetchall()
    return jsonify({'status':'ok','data':{'attendance':[
        {'id':r[0],'student_id':r[1],'subject':r[2],'date':r[3],'status':r[4]} for r in rows
    ]}})

@teacher_bp.route('/attendance/mark', methods=['POST'])
@teacher_required
def mark_attendance():
    d = request.get_json()
    # d = {subject, date, records: [{student_id, status}]}
    subject = d.get('subject')
    date    = d.get('date')
    records = d.get('records', [])
    if not subject or not date or not records:
        return jsonify({'error':'Missing fields'}), 400
    for rec in records:
        existing = db.execute(
            "SELECT id FROM attendance WHERE student_id=? AND subject=? AND date=?",
            (rec['student_id'], subject, date)
        ).fetchone()
        if existing:
            db.execute(
                "UPDATE attendance SET status=? WHERE id=?", (rec['status'], existing[0])
            )
        else:
            db.execute(
                "INSERT INTO attendance (student_id,subject,date,status,teacher_id) VALUES (?,?,?,?,?)",
                (rec['student_id'], subject, date, rec['status'], get_teacher_id())
            )
    db.commit()
    return jsonify({'status':'ok','message':f'Attendance marked for {len(records)} students'})

# ─── Assignments ──────────────────────────────────────────────────────────────
@teacher_bp.route('/assignments')
@teacher_required
def assignments():
    per_page = int(request.args.get('per_page', 20))
    rows = db.execute(
        "SELECT id,title,subject,due_date,status,description FROM assignments WHERE teacher_id=? ORDER BY due_date DESC LIMIT ?",
        (get_teacher_id(), per_page)
    ).fetchall()
    return jsonify({'status':'ok','data':{'assignments':[
        {'id':r[0],'title':r[1],'subject':r[2],'due_date':r[3],'status':r[4],'description':r[5]} for r in rows
    ]}})

@teacher_bp.route('/assignments/create', methods=['POST'])
@teacher_required
def create_assignment():
    d = request.get_json()
    required = ['title','subject','due_date','description']
    if not all(k in d for k in required):
        return jsonify({'error':'Missing fields'}), 400
    db.execute(
        "INSERT INTO assignments (title,subject,due_date,description,status,teacher_id,created_at) VALUES (?,?,?,?,?,?,?)",
        (d['title'],d['subject'],d['due_date'],d['description'],'Pending',get_teacher_id(),datetime.now().isoformat())
    )
    db.commit()
    return jsonify({'status':'ok','message':'Assignment created successfully'})

@teacher_bp.route('/assignments/<int:aid>', methods=['PUT'])
@teacher_required
def update_assignment(aid):
    d = request.get_json()
    db.execute(
        "UPDATE assignments SET title=?,subject=?,due_date=?,description=?,status=? WHERE id=? AND teacher_id=?",
        (d.get('title'),d.get('subject'),d.get('due_date'),d.get('description'),d.get('status'),aid,get_teacher_id())
    )
    db.commit()
    return jsonify({'status':'ok','message':'Assignment updated'})

@teacher_bp.route('/assignments/<int:aid>', methods=['DELETE'])
@teacher_required
def delete_assignment(aid):
    db.execute("DELETE FROM assignments WHERE id=? AND teacher_id=?", (aid, get_teacher_id()))
    db.commit()
    return jsonify({'status':'ok','message':'Assignment deleted'})

# ─── Notices ──────────────────────────────────────────────────────────────────
@teacher_bp.route('/notices')
@teacher_required
def notices():
    rows = db.execute(
        "SELECT id,title,content,priority,created_at,teacher_id FROM notices ORDER BY created_at DESC LIMIT 20"
    ).fetchall()
    return jsonify({'status':'ok','data':{'notices':[
        {'id':r[0],'title':r[1],'content':r[2],'priority':r[3],'created_at':r[4],'teacher_id':r[5]} for r in rows
    ]}})

@teacher_bp.route('/notices/post', methods=['POST'])
@teacher_required
def post_notice():
    d = request.get_json()
    if not d.get('title') or not d.get('content'):
        return jsonify({'error':'Title and content required'}), 400
    db.execute(
        "INSERT INTO notices (title,content,priority,teacher_id,created_at) VALUES (?,?,?,?,?)",
        (d['title'],d['content'],d.get('priority','Normal'),get_teacher_id(),datetime.now().isoformat())
    )
    db.commit()
    return jsonify({'status':'ok','message':'Notice posted successfully'})

@teacher_bp.route('/notices/<int:nid>', methods=['DELETE'])
@teacher_required
def delete_notice(nid):
    db.execute("DELETE FROM notices WHERE id=? AND teacher_id=?", (nid, get_teacher_id()))
    db.commit()
    return jsonify({'status':'ok','message':'Notice deleted'})

# ─── Messages ─────────────────────────────────────────────────────────────────
@teacher_bp.route('/messages')
@teacher_required
def messages():
    rows = db.execute(
        """SELECT m.id,m.sender_id,m.receiver_id,m.content,m.created_at,m.is_read,
                  u.name as sender_name
           FROM messages m JOIN users u ON m.sender_id=u.id
           WHERE m.receiver_id=? OR m.sender_id=?
           ORDER BY m.created_at DESC LIMIT 30""",
        (get_teacher_id(), get_teacher_id())
    ).fetchall()
    return jsonify({'status':'ok','data':{'messages':[
        {'id':r[0],'sender_id':r[1],'receiver_id':r[2],'content':r[3],'created_at':r[4],'is_read':r[5],'sender_name':r[6]} for r in rows
    ]}})

@teacher_bp.route('/messages/send', methods=['POST'])
@teacher_required
def send_message():
    d = request.get_json()
    if not d.get('receiver_id') or not d.get('content'):
        return jsonify({'error':'receiver_id and content required'}), 400
    db.execute(
        "INSERT INTO messages (sender_id,receiver_id,content,created_at,is_read) VALUES (?,?,?,?,?)",
        (get_teacher_id(), d['receiver_id'], d['content'], datetime.now().isoformat(), 0)
    )
    db.commit()
    return jsonify({'status':'ok','message':'Message sent'})

# ─── Statistics ───────────────────────────────────────────────────────────────
@teacher_bp.route('/statistics')
@teacher_required
def statistics():
    students  = db.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    total_asgn= db.execute("SELECT COUNT(*) FROM assignments WHERE teacher_id=?", (get_teacher_id(),)).fetchone()[0]
    submitted = db.execute("SELECT COUNT(*) FROM assignments WHERE teacher_id=? AND status='Submitted'", (get_teacher_id(),)).fetchone()[0]
    pending   = total_asgn - submitted
    results   = db.execute("SELECT COUNT(*) FROM results").fetchone()[0]
    total_att = db.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]
    present   = db.execute("SELECT COUNT(*) FROM attendance WHERE status='Present'").fetchone()[0]
    absent    = total_att - present
    pct       = round(present*100/total_att,1) if total_att else 0
    return jsonify({'status':'ok','data':{
        'students': students,
        'assignments':{'total':total_asgn,'submitted':submitted,'pending':pending},
        'results': results,
        'attendance':{'total':total_att,'present':present,'absent':absent,'percentage':pct}
    }})
