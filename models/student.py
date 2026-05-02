from models import db
from datetime import datetime

class Student(db.Model):
    __tablename__ = 'students'
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    roll_no     = db.Column(db.String(20), unique=True, nullable=False)
    branch      = db.Column(db.String(50))
    semester    = db.Column(db.Integer)
    batch       = db.Column(db.String(10))
    phone       = db.Column(db.String(15))
    dob         = db.Column(db.Date)
    blood_group = db.Column(db.String(5))
    address     = db.Column(db.Text)
    father_name = db.Column(db.String(100))
    cgpa        = db.Column(db.Float, default=0.0)
    photo       = db.Column(db.String(200))

class Attendance(db.Model):
    __tablename__ = 'attendance'
    id         = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'))
    subject    = db.Column(db.String(100))
    date       = db.Column(db.Date, default=datetime.utcnow)
    status     = db.Column(db.String(10))

class Result(db.Model):
    __tablename__ = 'results'
    id         = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'))
    subject    = db.Column(db.String(100))
    semester   = db.Column(db.Integer)
    internal   = db.Column(db.Float)
    external   = db.Column(db.Float)
    grade      = db.Column(db.String(5))

class Fee(db.Model):
    __tablename__ = 'fees'
    id          = db.Column(db.Integer, primary_key=True)
    student_id  = db.Column(db.Integer, db.ForeignKey('students.id'))
    description = db.Column(db.String(200))
    amount      = db.Column(db.Float)
    paid_on     = db.Column(db.DateTime, default=datetime.utcnow)
    status      = db.Column(db.String(20), default='paid')

class Assignment(db.Model):
    __tablename__ = 'assignments'
    id         = db.Column(db.Integer, primary_key=True)
    title      = db.Column(db.String(200))
    subject    = db.Column(db.String(100))
    due_date   = db.Column(db.Date)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'))
    status     = db.Column(db.String(20), default='pending')