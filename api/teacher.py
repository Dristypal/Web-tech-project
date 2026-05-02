from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models.student import Student, Attendance, Result, Assignment
from models.user import User
from models.notice import Notice
from models import db
from datetime import datetime, timedelta

teacher_bp = Blueprint('api_teacher', __name__, url_prefix='/api/teacher')

def success_response(data, status_code=200):
    return jsonify({'success': True, 'data': data, 'error': None}), status_code

def error_response(message, status_code=400):
    return jsonify({'success': False, 'data': None, 'error': message}), status_code

def check_teacher_exists():
    if not current_user.is_teacher():
        return None, error_response('Only teachers can access this', 403)
    return current_user, None

@teacher_bp.route('/dashboard', methods=['GET'])
@login_required
def get_dashboard():
    try:
        teacher, err = check_teacher_exists()
        if err: return err
        total_students = Student.query.count()
        total_assignments = Assignment.query.count()
        pending = Assignment.query.filter_by(status='Pending').count()
        submitted = Assignment.query.filter_by(status='Submitted').count()
        all_attendance = Attendance.query.all()
        avg_att = 0
        if all_attendance:
            present = len([a for a in all_attendance if a.status == 'Present'])
            avg_att = (present / len(all_attendance)) * 100
        return success_response({
            'teacher_info': {'name': teacher.name, 'email': teacher.email, 'role': teacher.role},
            'metrics': {'total_students': total_students, 'total_assignments': total_assignments,
                        'pending': pending, 'submitted': submitted, 'avg_attendance': round(avg_att, 2)},
            'recent_assignments': [{'id': a.id, 'title': a.title, 'subject': a.subject,
                'due_date': a.due_date.isoformat(), 'status': a.status}
                for a in Assignment.query.order_by(Assignment.due_date.desc()).limit(5).all()]
        })
    except Exception as e:
        return error_response(f'Error: {str(e)}', 500)

@teacher_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    try:
        teacher, err = check_teacher_exists()
        if err: return err
        return success_response({'id': teacher.id, 'name': teacher.name, 'email': teacher.email, 'role': teacher.role})
    except Exception as e:
        return error_response(f'Error: {str(e)}', 500)

@teacher_bp.route('/students', methods=['GET'])
@login_required
def get_students():
    try:
        teacher, err = check_teacher_exists()
        if err: return err
        search = request.args.get('search', '')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        query = Student.query.join(User).filter(User.name.ilike(f'%{search}%') if search else True)
        total = query.count()
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        students = [{'id': s.id, 'name': s.user.name if s.user else 'N/A',
                     'email': s.user.email if s.user else 'N/A',
                     'roll_no': s.roll_no, 'branch': s.branch,
                     'semester': s.semester, 'cgpa': s.cgpa} for s in paginated.items]
        return success_response({'students': students, 'pagination': {'total': total, 'page': page, 'per_page': per_page}})
    except Exception as e:
        return error_response(f'Error: {str(e)}', 500)

@teacher_bp.route('/students/<int:student_id>', methods=['GET'])
@login_required
def get_student_detail(student_id):
    try:
        teacher, err = check_teacher_exists()
        if err: return err
        student = Student.query.get(student_id)
        if not student: return error_response('Student not found', 404)
        att = Attendance.query.filter_by(student_id=student_id).all()
        present = len([a for a in att if a.status == 'Present'])
        att_pct = (present / len(att)) * 100 if att else 0
        results = Result.query.filter_by(student_id=student_id).all()
        assignments = Assignment.query.filter_by(student_id=student_id).all()
        return success_response({
            'student_info': {'id': student.id, 'name': student.user.name if student.user else 'N/A',
                             'email': student.user.email if student.user else 'N/A',
                             'roll_no': student.roll_no, 'branch': student.branch,
                             'semester': student.semester, 'cgpa': student.cgpa, 'phone': student.phone},
            'stats': {'attendance': round(att_pct, 2), 'total_att': len(att),
                      'total_results': len(results), 'total_assignments': len(assignments),
                      'submitted': len([a for a in assignments if a.status == 'Submitted'])}
        })
    except Exception as e:
        return error_response(f'Error: {str(e)}', 500)

@teacher_bp.route('/assignments', methods=['GET'])
@login_required
def get_assignments():
    try:
        teacher, err = check_teacher_exists()
        if err: return err
        status = request.args.get('status')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        query = Assignment.query
        if status: query = query.filter_by(status=status)
        total = query.count()
        paginated = query.order_by(Assignment.due_date.desc()).paginate(page=page, per_page=per_page, error_out=False)
        assignments = [{'id': a.id, 'title': a.title, 'subject': a.subject,
                        'due_date': a.due_date.isoformat(), 'status': a.status, 'student_id': a.student_id}
                       for a in paginated.items]
        return success_response({'assignments': assignments, 'pagination': {'total': total, 'page': page, 'per_page': per_page}})
    except Exception as e:
        return error_response(f'Error: {str(e)}', 500)

@teacher_bp.route('/assignments/create', methods=['POST'])
@login_required
def create_assignment():
    try:
        teacher, err = check_teacher_exists()
        if err: return err
        d = request.get_json()
        title = d.get('title', '').strip()
        subject = d.get('subject', '').strip()
        due_date = d.get('due_date', '')
        if not title or not subject or not due_date:
            return error_response('Title, subject and due_date are required', 400)
        due = datetime.strptime(due_date, '%Y-%m-%d')
        student_ids = d.get('student_ids') or [s.id for s in Student.query.all()]
        for sid in student_ids:
            db.session.add(Assignment(student_id=int(sid), title=title, subject=subject, due_date=due, status='Pending'))
        db.session.commit()
        return success_response({'message': f'Assignment created for {len(student_ids)} students'})
    except Exception as e:
        db.session.rollback()
        return error_response(f'Error: {str(e)}', 500)

@teacher_bp.route('/assignments/<int:aid>', methods=['PUT'])
@login_required
def update_assignment(aid):
    try:
        teacher, err = check_teacher_exists()
        if err: return err
        a = Assignment.query.get(aid)
        if not a: return error_response('Not found', 404)
        d = request.get_json()
        if d.get('title'): a.title = d['title']
        if d.get('subject'): a.subject = d['subject']
        if d.get('status'): a.status = d['status']
        if d.get('due_date'): a.due_date = datetime.strptime(d['due_date'], '%Y-%m-%d')
        db.session.commit()
        return success_response({'message': 'Updated'})
    except Exception as e:
        db.session.rollback()
        return error_response(f'Error: {str(e)}', 500)

@teacher_bp.route('/assignments/<int:aid>', methods=['DELETE'])
@login_required
def delete_assignment(aid):
    try:
        teacher, err = check_teacher_exists()
        if err: return err
        a = Assignment.query.get(aid)
        if not a: return error_response('Not found', 404)
        db.session.delete(a)
        db.session.commit()
        return success_response({'message': 'Deleted'})
    except Exception as e:
        db.session.rollback()
        return error_response(f'Error: {str(e)}', 500)

@teacher_bp.route('/results', methods=['GET'])
@login_required
def get_results():
    try:
        teacher, err = check_teacher_exists()
        if err: return err
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        total = Result.query.count()
        paginated = Result.query.paginate(page=page, per_page=per_page, error_out=False)
        results = [{'id': r.id, 'student_id': r.student_id, 'subject': r.subject,
                    'internal': r.internal, 'external': r.external, 'grade': r.grade, 'semester': r.semester}
                   for r in paginated.items]
        return success_response({'results': results, 'pagination': {'total': total, 'page': page, 'per_page': per_page}})
    except Exception as e:
        return error_response(f'Error: {str(e)}', 500)

@teacher_bp.route('/results/add', methods=['POST'])
@login_required
def add_result():
    try:
        teacher, err = check_teacher_exists()
        if err: return err
        d = request.get_json()
        r = Result(student_id=int(d['student_id']), subject=d['subject'],
                   internal=float(d['internal']), external=float(d['external']),
                   grade=d['grade'], semester=int(d['semester']))
        db.session.add(r)
        db.session.commit()
        return success_response({'message': 'Result added', 'id': r.id})
    except Exception as e:
        db.session.rollback()
        return error_response(f'Error: {str(e)}', 500)

@teacher_bp.route('/results/<int:rid>', methods=['PUT'])
@login_required
def update_result(rid):
    try:
        teacher, err = check_teacher_exists()
        if err: return err
        r = Result.query.get(rid)
        if not r: return error_response('Not found', 404)
        d = request.get_json()
        if 'subject' in d: r.subject = d['subject']
        if 'internal' in d: r.internal = float(d['internal'])
        if 'external' in d: r.external = float(d['external'])
        if 'grade' in d: r.grade = d['grade']
        if 'semester' in d: r.semester = int(d['semester'])
        db.session.commit()
        return success_response({'message': 'Updated'})
    except Exception as e:
        db.session.rollback()
        return error_response(f'Error: {str(e)}', 500)

@teacher_bp.route('/results/<int:rid>', methods=['DELETE'])
@login_required
def delete_result(rid):
    try:
        teacher, err = check_teacher_exists()
        if err: return err
        r = Result.query.get(rid)
        if not r: return error_response('Not found', 404)
        db.session.delete(r)
        db.session.commit()
        return success_response({'message': 'Deleted'})
    except Exception as e:
        db.session.rollback()
        return error_response(f'Error: {str(e)}', 500)

@teacher_bp.route('/attendance', methods=['GET'])
@login_required
def get_attendance():
    try:
        teacher, err = check_teacher_exists()
        if err: return err
        subject = request.args.get('subject')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        query = Attendance.query
        if subject: query = query.filter_by(subject=subject)
        total = query.count()
        paginated = query.order_by(Attendance.date.desc()).paginate(page=page, per_page=per_page, error_out=False)
        att = [{'id': a.id, 'student_id': a.student_id, 'subject': a.subject,
                'date': a.date.isoformat(), 'status': a.status} for a in paginated.items]
        return success_response({'attendance': att, 'pagination': {'total': total, 'page': page, 'per_page': per_page}})
    except Exception as e:
        return error_response(f'Error: {str(e)}', 500)

@teacher_bp.route('/attendance/mark', methods=['POST'])
@login_required
def mark_attendance():
    try:
        teacher, err = check_teacher_exists()
        if err: return err
        d = request.get_json()
        subject = d.get('subject', '').strip()
        date_str = d.get('date', '')
        records = d.get('records', [])
        if not subject or not date_str or not records:
            return error_response('subject, date and records required', 400)
        att_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        for rec in records:
            sid = int(rec['student_id'])
            status = rec.get('status', 'Present')
            existing = Attendance.query.filter_by(student_id=sid, subject=subject, date=att_date).first()
            if existing:
                existing.status = status
            else:
                db.session.add(Attendance(student_id=sid, subject=subject, date=att_date, status=status))
        db.session.commit()
        return success_response({'message': f'Attendance marked for {len(records)} students'})
    except Exception as e:
        db.session.rollback()
        return error_response(f'Error: {str(e)}', 500)

@teacher_bp.route('/notices', methods=['GET'])
@login_required
def get_notices():
    try:
        teacher, err = check_teacher_exists()
        if err: return err
        notices = Notice.query.order_by(Notice.date.desc()).limit(20).all()
        return success_response({'notices': [
            {'id': n.id, 'title': n.title, 'content': n.content,
             'category': getattr(n, 'category', 'General'),
             'posted_by': n.posted_by,
             'created_at': n.date.isoformat() if n.date else ''}
            for n in notices]})
    except Exception as e:
        return error_response(f'Error: {str(e)}', 500)

@teacher_bp.route('/notices/post', methods=['POST'])
@login_required
def post_notice():
    try:
        teacher, err = check_teacher_exists()
        if err: return err
        d = request.get_json()
        title = d.get('title', '').strip()
        content = d.get('content', '').strip()
        if not title or not content:
            return error_response('Title and content required', 400)
        n = Notice(title=title, content=content,
                   category=d.get('priority', 'General'),
                   posted_by=current_user.name, date=datetime.now())
        db.session.add(n)
        db.session.commit()
        return success_response({'message': 'Notice posted', 'id': n.id})
    except Exception as e:
        db.session.rollback()
        return error_response(f'Error: {str(e)}', 500)

@teacher_bp.route('/notices/<int:nid>', methods=['DELETE'])
@login_required
def delete_notice(nid):
    try:
        teacher, err = check_teacher_exists()
        if err: return err
        n = Notice.query.get(nid)
        if not n: return error_response('Not found', 404)
        db.session.delete(n)
        db.session.commit()
        return success_response({'message': 'Deleted'})
    except Exception as e:
        db.session.rollback()
        return error_response(f'Error: {str(e)}', 500)

@teacher_bp.route('/messages', methods=['GET'])
@login_required
def get_messages():
    try:
        teacher, err = check_teacher_exists()
        if err: return err
        notices = Notice.query.order_by(Notice.date.desc()).limit(20).all()
        return success_response({'messages': [
            {'id': n.id, 'sender_name': n.posted_by, 'content': n.content,
             'created_at': n.date.isoformat() if n.date else '', 'is_read': 1}
            for n in notices]})
    except Exception as e:
        return error_response(f'Error: {str(e)}', 500)

@teacher_bp.route('/messages/send', methods=['POST'])
@login_required
def send_message():
    try:
        teacher, err = check_teacher_exists()
        if err: return err
        d = request.get_json()
        content = d.get('content', '').strip()
        receiver_id = d.get('receiver_id')
        if not content: return error_response('Content required', 400)
        receiver = User.query.get(int(receiver_id)) if receiver_id else None
        n = Notice(title=f'Message to {receiver.name if receiver else "Student"}',
                   content=content, category='Message',
                   posted_by=current_user.name, date=datetime.now())
        db.session.add(n)
        db.session.commit()
        return success_response({'message': 'Message sent'})
    except Exception as e:
        db.session.rollback()
        return error_response(f'Error: {str(e)}', 500)

@teacher_bp.route('/statistics', methods=['GET'])
@login_required
def get_statistics():
    try:
        teacher, err = check_teacher_exists()
        if err: return err
        total_students = Student.query.count()
        total_assign = Assignment.query.count()
        total_results = Result.query.count()
        submitted = Assignment.query.filter_by(status='Submitted').count()
        pending = Assignment.query.filter_by(status='Pending').count()
        att_records = Attendance.query.all()
        present = len([a for a in att_records if a.status == 'Present'])
        avg_att = (present / len(att_records)) * 100 if att_records else 0
        return success_response({
            'students': total_students,
            'assignments': {'total': total_assign, 'submitted': submitted, 'pending': pending},
            'results': total_results,
            'attendance': {'total': len(att_records), 'present': present,
                           'absent': len(att_records) - present, 'percentage': round(avg_att, 2)}
        })
    except Exception as e:
        return error_response(f'Error: {str(e)}', 500)

@teacher_bp.route('/subjects', methods=['GET'])
@login_required
def get_subjects():
    try:
        teacher, err = check_teacher_exists()
        if err: return err
        all_subj = list(set(a.subject for a in Assignment.query.all() if a.subject) |
                        set(a.subject for a in Attendance.query.all() if a.subject) |
                        set(r.subject for r in Result.query.all() if r.subject))
        return success_response({'subjects': all_subj})
    except Exception as e:
        return error_response(f'Error: {str(e)}', 500)

@teacher_bp.errorhandler(404)
def not_found(e):
    return error_response('Endpoint not found', 404)

@teacher_bp.errorhandler(500)
def internal_error(e):
    return error_response('Internal server error', 500)
