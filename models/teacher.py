from models import db
from datetime import datetime

class TeacherProfile(db.Model):
    __tablename__ = 'teacher_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    qualification = db.Column(db.Text)
    experience_years = db.Column(db.Integer, default=0)
    specialization = db.Column(db.String(200))
    department = db.Column(db.String(100))
    research_papers = db.Column(db.Integer, default=0)
    publications = db.Column(db.Text)
    awards = db.Column(db.Text)
    bio = db.Column(db.Text)
    office_location = db.Column(db.String(100))
    office_phone = db.Column(db.String(20))
    office_hours = db.Column(db.String(500))
    availability_status = db.Column(db.Boolean, default=True)
    rating = db.Column(db.Float, default=0)
    total_reviews = db.Column(db.Integer, default=0)
    profile_photo = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TeacherReview(db.Model):
    __tablename__ = 'teacher_reviews'
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    overall_rating = db.Column(db.Integer)
    teaching_quality = db.Column(db.Integer)
    approachability = db.Column(db.Integer)
    knowledge = db.Column(db.Integer)
    comment = db.Column(db.Text)
    is_anonymous = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class MeetingRequest(db.Model):
    __tablename__ = 'meeting_requests'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    requested_date = db.Column(db.Date, nullable=False)
    requested_time = db.Column(db.String(10), nullable=False)
    topic = db.Column(db.String(300), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')
    teacher_response = db.Column(db.Text)
    meeting_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ClassMaterial(db.Model):
    __tablename__ = 'class_materials'
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(200))
    material_type = db.Column(db.String(50))
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_published = db.Column(db.Boolean, default=True)

class GradeComponent(db.Model):
    __tablename__ = 'grade_components'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    internal_marks = db.Column(db.Float)
    external_marks = db.Column(db.Float)
    practical_marks = db.Column(db.Float)
    project_marks = db.Column(db.Float)
    assignment_marks = db.Column(db.Float)
    teacher_feedback = db.Column(db.Text)
    improvement_areas = db.Column(db.Text)
    strengths = db.Column(db.Text)
    total_marks = db.Column(db.Float)
    grade = db.Column(db.String(5))
    date_issued = db.Column(db.DateTime, default=datetime.utcnow)
    semester = db.Column(db.Integer)

class StudentPerformance(db.Model):
    __tablename__ = 'student_performance'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    overall_cgpa = db.Column(db.Float, default=0)
    current_semester_gpa = db.Column(db.Float, default=0)
    total_credits = db.Column(db.Integer, default=0)
    passed_credits = db.Column(db.Integer, default=0)
    failed_courses = db.Column(db.Integer, default=0)
    attendance_percentage = db.Column(db.Float, default=0)
    rank_in_class = db.Column(db.Integer)
    total_students = db.Column(db.Integer)
    improvement_trend = db.Column(db.String(20))
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50))
    related_id = db.Column(db.Integer)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(200))
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)