from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models.user import User
from models.student import Student
from models import db

admin_bp = Blueprint('api_admin', __name__, url_prefix='/api/admin')

def success(data, code=200):
    return jsonify({'success': True, 'data': data, 'error': None}), code

def error(msg, code=400):
    return jsonify({'success': False, 'data': None, 'error': msg}), code

def admin_only():
    if not current_user.is_authenticated or current_user.role != 'admin':
        return False
    return True


@admin_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    if not admin_only():
        return error('Admin access required', 403)
    total_users = User.query.count()
    total_students = User.query.filter_by(role='student').count()
    total_teachers = User.query.filter_by(role='teacher').count()
    return success({'total_users': total_users, 'students': total_students, 'teachers': total_teachers})


@admin_bp.route('/users', methods=['GET'])
@login_required
def list_users():
    if not admin_only():
        return error('Admin access required', 403)
    users = User.query.order_by(User.created_at.desc()).all()
    out = []
    for u in users:
        out.append({'id': u.id, 'name': u.name, 'email': u.email, 'role': u.role})
    return success(out)


@admin_bp.route('/users/<int:uid>/promote', methods=['POST'])
@login_required
def promote_user(uid):
    if not admin_only():
        return error('Admin access required', 403)
    user = User.query.get_or_404(uid)
    new_role = request.json.get('role') if request.is_json else request.form.get('role')
    if new_role not in ('student', 'teacher', 'admin'):
        return error('Invalid role', 400)
    user.role = new_role
    db.session.commit()
    return success({'id': user.id, 'role': user.role})


@admin_bp.route('/users/<int:uid>/delete', methods=['POST'])
@login_required
def delete_user(uid):
    if not admin_only():
        return error('Admin access required', 403)
    user = User.query.get_or_404(uid)
    db.session.delete(user)
    db.session.commit()
    return success({'message': 'User deleted'})
