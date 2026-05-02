"""
Teacher API Blueprint - All endpoints for teacher module
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models.user import User
from models.student import Student, Attendance, Result, Fee, Assignment
from datetime import datetime, timedelta

teacher_bp = Blueprint('api_teacher', __name__, url_prefix='/api/teacher')

def success_response(data, status_code=200):
    return jsonify({
        'success': True,
        'data': data,
        'error': None
    }), status_code

def error_response(message, status_code=400):
    return jsonify({
        'success': False,
        'data': None,
        'error': message
    }), status_code

def check_teacher_exists():
    """Check if user is a teacher"""
    if not current_user.is_teacher():
        return None, error_response('Only teachers can access this', 403)
    return current_user, None

# ============================================================================
# 1. DASHBOARD ENDPOINT
# ============================================================================

@teacher_bp.route('/dashboard', methods=['GET'])
@login_required
def get_dashboard():
    """
    Get teacher dashboard overview
    GET /api/teacher/dashboard
    """
    try:
        teacher, err = check_teacher_exists()
        if err:
            return err
        
        # Get all students (assuming teacher teaches all students for now)
        total_students = Student.query.count()
        total_assignments = Assignment.query.count()
        pending_submissions = Assignment.query.filter_by(status='Pending').count()
        submitted = Assignment.query.filter_by(status='Submitted').count()
        
        # Get average attendance
        all_attendance = Attendance.query.all()
        avg_attendance = 0
        if all_attendance:
            present = len([a for a in all_attendance if a.status == 'Present'])
            avg_attendance = (present / len(all_attendance)) * 100
        
        dashboard_data = {
            'teacher_info': {
                'name': teacher.name,
                'email': teacher.email,
                'role': teacher.role
            },
            'metrics': {
                'total_students': total_students,
                'total_assignments': total_assignments,
                'pending_submissions': pending_submissions,
                'submitted': submitted,
                'average_attendance': round(avg_attendance, 2)
            },
            'recent_assignments': [{
                'id': a.id,
                'title': a.title,
                'subject': a.subject,
                'due_date': a.due_date.isoformat(),
                'status': a.status
            } for a in Assignment.query.order_by(Assignment.due_date.desc()).limit(5).all()]
        }
        
        return success_response(dashboard_data)
    
    except Exception as e:
        return error_response(f'Error fetching dashboard: {str(e)}', 500)

# ============================================================================
# 2. PROFILE ENDPOINTS
# ============================================================================

@teacher_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """
    Get teacher profile
    GET /api/teacher/profile
    """
    try:
        teacher, err = check_teacher_exists()
        if err:
            return err
        
        profile_data = {
            'id': teacher.id,
            'name': teacher.name,
            'email': teacher.email,
            'role': teacher.role,
            'created_at': teacher.created_at.isoformat() if hasattr(teacher, 'created_at') else None
        }
        
        return success_response(profile_data)
    
    except Exception as e:
        return error_response(f'Error fetching profile: {str(e)}', 500)

@teacher_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    """
    Update teacher profile
    POST /api/teacher/profile/update
    Body: {
        "name": "Dr. New Name",
        "email": "newemail@campus.edu"
    }
    """
    try:
        teacher, err = check_teacher_exists()
        if err:
            return err
        
        data = request.get_json()
        
        if 'name' in data:
            teacher.name = data['name']
        if 'email' in data:
            teacher.email = data['email']
        
        from models import db
        db.session.commit()
        
        return success_response({'message': 'Profile updated successfully'})
    
    except Exception as e:
        return error_response(f'Error updating profile: {str(e)}', 500)

# ============================================================================
# 3. STUDENTS ENDPOINTS
# ============================================================================

@teacher_bp.route('/students', methods=['GET'])
@login_required
def get_students():
    """
    Get all students (with pagination and search)
    GET /api/teacher/students?page=1&per_page=10&search=John
    """
    try:
        teacher, err = check_teacher_exists()
        if err:
            return err
        
        search = request.args.get('search', '')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Build query
        query = Student.query.join(User).filter(
            User.name.ilike(f'%{search}%') if search else True
        )
        
        total = query.count()
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        students_data = [{
            'id': s.id,
            'user_id': s.user_id,
            'name': s.user.name if s.user else 'N/A',
            'email': s.user.email if s.user else 'N/A',
            'roll_no': s.roll_no,
            'branch': s.branch,
            'semester': s.semester,
            'cgpa': s.cgpa
        } for s in paginated.items]
        
        return success_response({
            'students': students_data,
            'pagination': {
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }
        })
    
    except Exception as e:
        return error_response(f'Error fetching students: {str(e)}', 500)

@teacher_bp.route('/students/<int:student_id>', methods=['GET'])
@login_required
def get_student_detail(student_id):
    """
    Get specific student details
    GET /api/teacher/students/1
    """
    try:
        teacher, err = check_teacher_exists()
        if err:
            return err
        
        student = Student.query.filter_by(id=student_id).first()
        if not student:
            return error_response('Student not found', 404)
        
        # Get student stats
        attendance_records = Attendance.query.filter_by(student_id=student_id).all()
        present_count = len([a for a in attendance_records if a.status == 'Present'])
        attendance_pct = (present_count / len(attendance_records)) * 100 if attendance_records else 0
        
        results = Result.query.filter_by(student_id=student_id).all()
        assignments = Assignment.query.filter_by(student_id=student_id).all()
        
        student_detail = {
            'student_info': {
                'id': student.id,
                'name': student.user.name if student.user else 'N/A',
                'email': student.user.email if student.user else 'N/A',
                'roll_no': student.roll_no,
                'branch': student.branch,
                'semester': student.semester,
                'cgpa': student.cgpa,
                'phone': student.phone
            },
            'statistics': {
                'attendance_percentage': round(attendance_pct, 2),
                'total_attendance': len(attendance_records),
                'total_results': len(results),
                'total_assignments': len(assignments),
                'assignment_completion': len([a for a in assignments if a.status == 'Submitted'])
            },
            'recent_results': [{
                'subject': r.subject,
                'internal': r.internal,
                'external': r.external,
                'grade': r.grade
            } for r in results[-5:]],
            'recent_assignments': [{
                'title': a.title,
                'status': a.status,
                'due_date': a.due_date.isoformat()
            } for a in assignments[-5:]]
        }
        
        return success_response(student_detail)
    
    except Exception as e:
        return error_response(f'Error fetching student: {str(e)}', 500)

# ============================================================================
# 4. ASSIGNMENTS ENDPOINTS
# ============================================================================

@teacher_bp.route('/assignments', methods=['GET'])
@login_required
def get_assignments():
    """
    Get all assignments with filtering
    GET /api/teacher/assignments?status=Pending&page=1
    """
    try:
        teacher, err = check_teacher_exists()
        if err:
            return err
        
        status = request.args.get('status')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        query = Assignment.query
        if status:
            query = query.filter_by(status=status)
        
        total = query.count()
        paginated = query.order_by(Assignment.due_date.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        assignments_data = [{
            'id': a.id,
            'title': a.title,
            'subject': a.subject,
            'due_date': a.due_date.isoformat(),
            'status': a.status,
            'student_id': a.student_id
        } for a in paginated.items]
        
        return success_response({
            'assignments': assignments_data,
            'pagination': {
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }
        })
    
    except Exception as e:
        return error_response(f'Error fetching assignments: {str(e)}', 500)

@teacher_bp.route('/assignments/create', methods=['POST'])
@login_required
def create_assignment():
    """
    Create new assignment
    POST /api/teacher/assignments/create
    Body: {
        "title": "Assignment 1",
        "subject": "Data Structures",
        "due_date": "2026-05-15T00:00:00",
        "student_id": 1
    }
    """
    try:
        teacher, err = check_teacher_exists()
        if err:
            return err
        
        data = request.get_json()
        
        required_fields = ['title', 'subject', 'due_date', 'student_id']
        for field in required_fields:
            if field not in data:
                return error_response(f'Missing field: {field}', 400)
        
        from models import db
        
        assignment = Assignment(
            student_id=data['student_id'],
            subject=data['subject'],
            title=data['title'],
            due_date=datetime.fromisoformat(data['due_date']),
            status='Pending'
        )
        
        db.session.add(assignment)
        db.session.commit()
        
        return success_response({
            'id': assignment.id,
            'message': 'Assignment created successfully'
        }, 201)
    
    except Exception as e:
        return error_response(f'Error creating assignment: {str(e)}', 500)

@teacher_bp.route('/assignments/<int:assignment_id>/grade', methods=['POST'])
@login_required
def grade_assignment(assignment_id):
    """
    Grade an assignment
    POST /api/teacher/assignments/1/grade
    Body: {
        "marks": 18,
        "feedback": "Good work!"
    }
    """
    try:
        teacher, err = check_teacher_exists()
        if err:
            return err
        
        assignment = Assignment.query.filter_by(id=assignment_id).first()
        if not assignment:
            return error_response('Assignment not found', 404)
        
        data = request.get_json()
        assignment.status = 'Submitted'
        
        from models import db
        db.session.commit()
        
        return success_response({'message': 'Assignment graded successfully'})
    
    except Exception as e:
        return error_response(f'Error grading assignment: {str(e)}', 500)

# ============================================================================
# 5. RESULTS ENDPOINTS
# ============================================================================

@teacher_bp.route('/results', methods=['GET'])
@login_required
def get_results():
    """
    Get all results with filtering
    GET /api/teacher/results?semester=5&page=1
    """
    try:
        teacher, err = check_teacher_exists()
        if err:
            return err
        
        semester = request.args.get('semester', type=int)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        query = Result.query
        if semester:
            query = query.filter_by(semester=semester)
        
        total = query.count()
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        results_data = [{
            'id': r.id,
            'student_id': r.student_id,
            'subject': r.subject,
            'internal': r.internal,
            'external': r.external,
            'grade': r.grade,
            'semester': r.semester
        } for r in paginated.items]
        
        return success_response({
            'results': results_data,
            'pagination': {
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }
        })
    
    except Exception as e:
        return error_response(f'Error fetching results: {str(e)}', 500)

@teacher_bp.route('/results/create', methods=['POST'])
@login_required
def create_result():
    """
    Create/Update student result
    POST /api/teacher/results/create
    Body: {
        "student_id": 1,
        "subject": "Data Structures",
        "internal": 35,
        "external": 65,
        "grade": "A",
        "semester": 5
    }
    """
    try:
        teacher, err = check_teacher_exists()
        if err:
            return err
        
        data = request.get_json()
        
        required_fields = ['student_id', 'subject', 'internal', 'external', 'grade', 'semester']
        for field in required_fields:
            if field not in data:
                return error_response(f'Missing field: {field}', 400)
        
        from models import db
        
        # Check if result exists
        existing = Result.query.filter_by(
            student_id=data['student_id'],
            subject=data['subject'],
            semester=data['semester']
        ).first()
        
        if existing:
            existing.internal = data['internal']
            existing.external = data['external']
            existing.grade = data['grade']
        else:
            result = Result(
                student_id=data['student_id'],
                subject=data['subject'],
                internal=data['internal'],
                external=data['external'],
                grade=data['grade'],
                semester=data['semester']
            )
            db.session.add(result)
        
        db.session.commit()
        
        return success_response({
            'message': 'Result created/updated successfully'
        }, 201)
    
    except Exception as e:
        return error_response(f'Error creating result: {str(e)}', 500)

# ============================================================================
# 6. ATTENDANCE ENDPOINTS
# ============================================================================

@teacher_bp.route('/attendance', methods=['GET'])
@login_required
def get_attendance():
    """
    Get attendance records
    GET /api/teacher/attendance?subject=Data Structures&page=1
    """
    try:
        teacher, err = check_teacher_exists()
        if err:
            return err
        
        subject = request.args.get('subject')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        query = Attendance.query
        if subject:
            query = query.filter_by(subject=subject)
        
        total = query.count()
        paginated = query.order_by(Attendance.date.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        attendance_data = [{
            'id': a.id,
            'student_id': a.student_id,
            'subject': a.subject,
            'date': a.date.isoformat(),
            'status': a.status
        } for a in paginated.items]
        
        return success_response({
            'attendance': attendance_data,
            'pagination': {
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }
        })
    
    except Exception as e:
        return error_response(f'Error fetching attendance: {str(e)}', 500)

@teacher_bp.route('/attendance/mark', methods=['POST'])
@login_required
def mark_attendance():
    """
    Mark attendance for student
    POST /api/teacher/attendance/mark
    Body: {
        "student_id": 1,
        "subject": "Data Structures",
        "status": "Present",
        "date": "2026-04-30"
    }
    """
    try:
        teacher, err = check_teacher_exists()
        if err:
            return err
        
        data = request.get_json()
        
        required_fields = ['student_id', 'subject', 'status', 'date']
        for field in required_fields:
            if field not in data:
                return error_response(f'Missing field: {field}', 400)
        
        from models import db
        
        attendance = Attendance(
            student_id=data['student_id'],
            subject=data['subject'],
            date=datetime.fromisoformat(data['date']),
            status=data['status']
        )
        
        db.session.add(attendance)
        db.session.commit()
        
        return success_response({
            'id': attendance.id,
            'message': 'Attendance marked successfully'
        }, 201)
    
    except Exception as e:
        return error_response(f'Error marking attendance: {str(e)}', 500)

# ============================================================================
# 7. STATISTICS ENDPOINTS
# ============================================================================

@teacher_bp.route('/statistics', methods=['GET'])
@login_required
def get_statistics():
    """
    Get overall statistics for teacher
    GET /api/teacher/statistics
    """
    try:
        teacher, err = check_teacher_exists()
        if err:
            return err
        
        total_students = Student.query.count()
        total_assignments = Assignment.query.count()
        total_results = Result.query.count()
        
        submitted_assignments = Assignment.query.filter_by(status='Submitted').count()
        pending_assignments = Assignment.query.filter_by(status='Pending').count()
        
        attendance_records = Attendance.query.all()
        present = len([a for a in attendance_records if a.status == 'Present'])
        avg_attendance = (present / len(attendance_records)) * 100 if attendance_records else 0
        
        stats = {
            'students': {
                'total': total_students
            },
            'assignments': {
                'total': total_assignments,
                'submitted': submitted_assignments,
                'pending': pending_assignments
            },
            'results': {
                'total': total_results
            },
            'attendance': {
                'total_records': len(attendance_records),
                'present': present,
                'absent': len(attendance_records) - present,
                'percentage': round(avg_attendance, 2)
            }
        }
        
        return success_response(stats)
    
    except Exception as e:
        return error_response(f'Error fetching statistics: {str(e)}', 500)

# ============================================================================
# 8. CLASS/SUBJECT ENDPOINTS
# ============================================================================

@teacher_bp.route('/subjects', methods=['GET'])
@login_required
def get_subjects():
    """
    Get all subjects being taught
    GET /api/teacher/subjects
    """
    try:
        teacher, err = check_teacher_exists()
        if err:
            return err
        
        # Get unique subjects from assignments and attendance
        assignment_subjects = set(a.subject for a in Assignment.query.all() if a.subject)
        attendance_subjects = set(a.subject for a in Attendance.query.all() if a.subject)
        result_subjects = set(r.subject for r in Result.query.all() if r.subject)
        
        all_subjects = list(assignment_subjects | attendance_subjects | result_subjects)
        
        return success_response({'subjects': all_subjects})
    
    except Exception as e:
        return error_response(f'Error fetching subjects: {str(e)}', 500)

@teacher_bp.route('/classes/<subject>', methods=['GET'])
@login_required
def get_class_details(subject):
    """
    Get all students in a specific subject/class
    GET /api/teacher/classes/Data Structures
    """
    try:
        teacher, err = check_teacher_exists()
        if err:
            return err
        
        # Get all students who have this subject
        attendance = Attendance.query.filter_by(subject=subject).all()
        student_ids = set(a.student_id for a in attendance)
        
        students = Student.query.filter(Student.id.in_(student_ids)).all()
        
        students_data = [{
            'id': s.id,
            'name': s.user.name if s.user else 'N/A',
            'roll_no': s.roll_no,
            'branch': s.branch
        } for s in students]
        
        return success_response({
            'subject': subject,
            'total_students': len(students_data),
            'students': students_data
        })
    
    except Exception as e:
        return error_response(f'Error fetching class details: {str(e)}', 500)

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@teacher_bp.errorhandler(404)
def not_found(e):
    return error_response('Endpoint not found', 404)

@teacher_bp.errorhandler(500)
def internal_error(e):
    return error_response('Internal server error', 500)