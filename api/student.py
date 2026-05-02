"""
Student API Blueprint - All endpoints for student module
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models.user import User
from models.student import Student, Attendance, Result, Fee, Assignment
from datetime import datetime, timedelta
import json

student_bp = Blueprint('api_student', __name__, url_prefix='/api/student')

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

def check_student_exists():
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        return None, error_response('Student profile not found', 404)
    return student, None

@student_bp.route('/dashboard', methods=['GET'])
@login_required
def get_dashboard():
    try:
        student, err = check_student_exists()
        if err:
            return err
        
        attendance_records = Attendance.query.filter_by(student_id=student.id).all()
        if attendance_records:
            present_count = len([a for a in attendance_records if a.status == 'Present'])
            attendance_pct = (present_count / len(attendance_records)) * 100
        else:
            attendance_pct = 0
        
        latest_results = Result.query.filter_by(student_id=student.id).order_by(Result.id.desc()).limit(3).all()
        pending_assignments = Assignment.query.filter_by(student_id=student.id).filter(Assignment.due_date > datetime.now(), Assignment.status != 'Submitted').count()
        fee = Fee.query.filter_by(student_id=student.id).first()
        
        dashboard_data = {
            'student_info': {
                'name': current_user.name,
                'email': current_user.email,
                'roll_no': student.roll_no,
                'branch': student.branch,
                'semester': student.semester,
                'cgpa': student.cgpa,
                'phone': student.phone
            },
            'metrics': {
                'attendance_percentage': round(attendance_pct, 2),
                'total_attendance': len(attendance_records),
                'pending_assignments': pending_assignments,
                'cgpa': student.cgpa
            },
            'recent_results': [{'id': r.id, 'subject': r.subject, 'internal': r.internal, 'external': r.external, 'total': r.internal + r.external, 'grade': r.grade} for r in latest_results],
            'fee_status': {'status': fee.status if fee else 'Not Found', 'amount': fee.amount if fee else 0, 'paid_on': fee.paid_on.isoformat() if fee and fee.paid_on else None}
        }
        
        return success_response(dashboard_data)
    
    except Exception as e:
        return error_response(f'Error fetching dashboard: {str(e)}', 500)

@student_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    try:
        student, err = check_student_exists()
        if err:
            return err
        
        profile_data = {
            'id': student.id,
            'user_id': student.user_id,
            'name': current_user.name,
            'email': current_user.email,
            'roll_no': student.roll_no,
            'branch': student.branch,
            'semester': student.semester,
            'cgpa': student.cgpa,
            'phone': student.phone
        }
        
        return success_response(profile_data)
    
    except Exception as e:
        return error_response(f'Error fetching profile: {str(e)}', 500)

@student_bp.route('/attendance', methods=['GET'])
@login_required
def get_attendance():
    try:
        student, err = check_student_exists()
        if err:
            return err
        
        subject = request.args.get('subject')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        query = Attendance.query.filter_by(student_id=student.id)
        if subject:
            query = query.filter_by(subject=subject)
        
        total = query.count()
        paginated = query.order_by(Attendance.date.desc()).paginate(page=page, per_page=per_page, error_out=False)
        
        attendance_data = [{'id': att.id, 'subject': att.subject, 'date': att.date.isoformat(), 'status': att.status} for att in paginated.items]
        
        all_attendance = Attendance.query.filter_by(student_id=student.id)
        if subject:
            all_attendance = all_attendance.filter_by(subject=subject)
        
        all_records = all_attendance.all()
        present_count = len([a for a in all_records if a.status == 'Present'])
        attendance_pct = (present_count / len(all_records)) * 100 if all_records else 0
        
        response_data = {
            'attendance': attendance_data,
            'pagination': {'total': total, 'page': page, 'per_page': per_page, 'total_pages': (total + per_page - 1) // per_page},
            'summary': {'total_classes': len(all_records), 'present': present_count, 'absent': len(all_records) - present_count, 'percentage': round(attendance_pct, 2)}
        }
        
        return success_response(response_data)
    
    except Exception as e:
        return error_response(f'Error fetching attendance: {str(e)}', 500)

@student_bp.route('/results', methods=['GET'])
@login_required
def get_results():
    try:
        student, err = check_student_exists()
        if err:
            return err
        
        semester = request.args.get('semester', type=int)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        query = Result.query.filter_by(student_id=student.id)
        if semester:
            query = query.filter_by(semester=semester)
        
        total = query.count()
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        results_data = [{'id': r.id, 'subject': r.subject, 'internal': r.internal, 'external': r.external, 'total': r.internal + r.external, 'grade': r.grade, 'semester': r.semester} for r in paginated.items]
        
        all_results = Result.query.filter_by(student_id=student.id).all()
        cgpa = student.cgpa if student.cgpa else 0
        
        response_data = {
            'results': results_data,
            'pagination': {'total': total, 'page': page, 'per_page': per_page, 'total_pages': (total + per_page - 1) // per_page},
            'summary': {'total_subjects': len(all_results), 'cgpa': cgpa}
        }
        
        return success_response(response_data)
    
    except Exception as e:
        return error_response(f'Error fetching results: {str(e)}', 500)

@student_bp.route('/assignments', methods=['GET'])
@login_required
def get_assignments():
    try:
        student, err = check_student_exists()
        if err:
            return err
        
        status = request.args.get('status')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        query = Assignment.query.filter_by(student_id=student.id)
        if status:
            query = query.filter_by(status=status)
        
        total = query.count()
        paginated = query.order_by(Assignment.due_date.desc()).paginate(page=page, per_page=per_page, error_out=False)
        
        assignments_data = [{'id': a.id, 'title': a.title, 'subject': a.subject, 'due_date': a.due_date.isoformat(), 'status': a.status} for a in paginated.items]
        
        response_data = {
            'assignments': assignments_data,
            'pagination': {'total': total, 'page': page, 'per_page': per_page, 'total_pages': (total + per_page - 1) // per_page}
        }
        
        return success_response(response_data)
    
    except Exception as e:
        return error_response(f'Error fetching assignments: {str(e)}', 500)

@student_bp.route('/fees', methods=['GET'])
@login_required
def get_fees():
    try:
        student, err = check_student_exists()
        if err:
            return err
        
        fees = Fee.query.filter_by(student_id=student.id).all()
        if not fees:
            return success_response({'fees': [], 'total_amount': 0, 'paid_amount': 0})
        
        fees_data = [{'id': f.id, 'description': f.description, 'amount': f.amount, 'status': f.status, 'paid_on': f.paid_on.isoformat() if f.paid_on else None} for f in fees]
        
        total_amount = sum(f.amount for f in fees)
        paid_amount = sum(f.amount for f in fees if f.status == 'Paid')
        pending_amount = total_amount - paid_amount
        
        response_data = {
            'fees': fees_data,
            'summary': {'total_amount': total_amount, 'paid_amount': paid_amount, 'pending_amount': pending_amount, 'payment_status': 'Paid' if pending_amount == 0 else 'Pending'}
        }
        
        return success_response(response_data)
    
    except Exception as e:
        return error_response(f'Error fetching fees: {str(e)}', 500)

@student_bp.route('/statistics', methods=['GET'])
@login_required
def get_statistics():
    try:
        student, err = check_student_exists()
        if err:
            return err
        
        attendance_records = Attendance.query.filter_by(student_id=student.id).all()
        present_count = len([a for a in attendance_records if a.status == 'Present'])
        attendance_pct = (present_count / len(attendance_records)) * 100 if attendance_records else 0
        
        results = Result.query.filter_by(student_id=student.id).all()
        avg_internal = sum(r.internal for r in results) / len(results) if results else 0
        avg_external = sum(r.external for r in results) / len(results) if results else 0
        
        all_assignments = Assignment.query.filter_by(student_id=student.id).all()
        submitted = len([a for a in all_assignments if a.status == 'Submitted'])
        pending = len([a for a in all_assignments if a.status == 'Pending'])
        
        fees = Fee.query.filter_by(student_id=student.id).all()
        total_fees = sum(f.amount for f in fees)
        paid_fees = sum(f.amount for f in fees if f.status == 'Paid')
        
        stats = {
            'attendance': {'total_classes': len(attendance_records), 'present': present_count, 'absent': len(attendance_records) - present_count, 'percentage': round(attendance_pct, 2)},
            'results': {'total_subjects': len(results), 'avg_internal': round(avg_internal, 2), 'avg_external': round(avg_external, 2), 'cgpa': student.cgpa},
            'assignments': {'total': len(all_assignments), 'submitted': submitted, 'pending': pending},
            'fees': {'total': total_fees, 'paid': paid_fees, 'pending': total_fees - paid_fees}
        }
        
        return success_response(stats)
    
    except Exception as e:
        return error_response(f'Error fetching statistics: {str(e)}', 500)

@student_bp.errorhandler(404)
def not_found(e):
    return error_response('Endpoint not found', 404)

@student_bp.errorhandler(500)
def internal_error(e):
    return error_response('Internal server error', 500)
