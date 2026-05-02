from models import db
from datetime import datetime

class Book(db.Model):
    __tablename__ = 'books'
    id         = db.Column(db.Integer, primary_key=True)
    title      = db.Column(db.String(200), nullable=False)
    author     = db.Column(db.String(100))
    isbn       = db.Column(db.String(20))
    category   = db.Column(db.String(50))
    copies     = db.Column(db.Integer, default=1)
    available  = db.Column(db.Integer, default=1)

class BorrowRecord(db.Model):
    __tablename__ = 'borrow_records'
    id          = db.Column(db.Integer, primary_key=True)
    student_id  = db.Column(db.Integer, db.ForeignKey('students.id'))
    book_id     = db.Column(db.Integer, db.ForeignKey('books.id'))
    borrow_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date    = db.Column(db.Date)
    return_date = db.Column(db.DateTime)
    status      = db.Column(db.String(20), default='borrowed')