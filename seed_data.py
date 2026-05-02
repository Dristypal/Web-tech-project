"""
Seed the database with demo data
"""

from app import app, db
from models.user import User
from models.student import Student, Attendance, Result, Fee, Assignment
from models.notice import Notice, Event
from models.library import Book, BorrowRecord
from datetime import datetime, timedelta

def seed_database():
    with app.app_context():
        # Clear existing data
        db.drop_all()
        db.create_all()
        
        print("🌱 Seeding database...")
        
        # Student User
        student_user = User(name='Dristy Pal', email='student@campus.edu', role='student')
        student_user.set_password('student123')
        db.session.add(student_user)
        db.session.flush()
        
        # Create Student Profile
        student = Student(
            user_id=student_user.id,
            roll_no='CS21B001',
            branch='B.Tech CSE',
            semester=5,
            cgpa=8.5,
            phone='9876543210'
        )
        db.session.add(student)
        
        # Teacher User
        teacher_user = User(name='Dr. Priya Sharma', email='teacher@campus.edu', role='teacher')
        teacher_user.set_password('teacher123')
        db.session.add(teacher_user)
        
        # Admin User
        admin_user = User(name='Admin User', email='admin@campus.edu', role='admin')
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        
        db.session.commit()
        print("✅ Users created")
        
        # Create Attendance Records
        subjects = ['Data Structures', 'Database Systems', 'Web Development', 'Machine Learning', 'Algorithms']
        
        for i, subject in enumerate(subjects):
            for day in range(20):
                attendance = Attendance(
                    student_id=student.id,
                    subject=subject,
                    date=datetime.now() - timedelta(days=day),
                    status='Present' if day % 3 != 0 else 'Absent'
                )
                db.session.add(attendance)
        
        db.session.commit()
        print("✅ Attendance records created")
        
        # Create Results
        for i, subject in enumerate(subjects):
            result = Result(
                student_id=student.id,
                subject=subject,
                internal=35 + (i * 2),
                external=65 + (i * 1),
                grade='A' if i % 2 == 0 else 'A+',
                semester=5
            )
            db.session.add(result)
        
        db.session.commit()
        print("✅ Results created")
        
        # Create Fees
        fee = Fee(
            student_id=student.id,
            amount=150000,
            due_date=datetime.now() + timedelta(days=30),
            paid_date=datetime.now() - timedelta(days=10),
            status='Paid',
            semester=5
        )
        db.session.add(fee)
        db.session.commit()
        print("✅ Fee records created")
        
        # Create Assignments
        assignment_subjects = ['Data Structures', 'Database Systems', 'Web Development']
        
        for i, subject in enumerate(assignment_subjects):
            assignment = Assignment(
                student_id=student.id,
                subject=subject,
                title=f'{subject} Assignment {i+1}',
                description=f'Complete the {subject} assignment',
                due_date=datetime.now() + timedelta(days=10+i),
                submitted_date=datetime.now() + timedelta(days=8+i),
                marks_obtained=18 + i,
                total_marks=20,
                status='Submitted'
            )
            db.session.add(assignment)
        
        db.session.commit()
        print("✅ Assignments created")
        
        # Create Notices
        notices = [
            Notice(
                title='Mid-Semester Exams Schedule',
                content='Mid-semester exams will be held from 15th May to 25th May 2026.',
                category='Academic',
                date=datetime.now() - timedelta(days=5)
            ),
            Notice(
                title='Library Extended Hours',
                content='The library will remain open until 10 PM during exam season.',
                category='General',
                date=datetime.now() - timedelta(days=2)
            ),
            Notice(
                title='Semester Project Submission',
                content='All semester projects must be submitted by 31st May.',
                category='Academic',
                date=datetime.now() - timedelta(days=1)
            ),
            Notice(
                title='Campus Placement Drive',
                content='Top IT companies visiting campus on 10th June.',
                category='Placement',
                date=datetime.now()
            ),
        ]
        
        for notice in notices:
            db.session.add(notice)
        
        db.session.commit()
        print("✅ Notices created")
        
        # Create Events
        events = [
            Event(
                title='Annual Tech Fest 2026',
                description='3-day tech festival with coding competitions, hackathons',
                date=datetime.now() + timedelta(days=20),
                category='Technical'
            ),
            Event(
                title='Sports Day',
                description='Inter-class sports competitions',
                date=datetime.now() + timedelta(days=30),
                category='Sports'
            ),
            Event(
                title='Guest Lecture: AI in Industry',
                description='Industry expert talk on applications of AI',
                date=datetime.now() + timedelta(days=15),
                category='Academic'
            ),
        ]
        
        for event in events:
            db.session.add(event)
        
        db.session.commit()
        print("✅ Events created")
        
        # Create Library Books
        books = [
            Book(
                title='Introduction to Algorithms',
                author='Cormen, Leiserson, Rivest, Stein',
                isbn='9780262033848',
                category='Computer Science',
                available_copies=3,
                total_copies=5
            ),
            Book(
                title='Database Design and Implementation',
                author='Edward Sciore',
                isbn='9783030334635',
                category='Database',
                available_copies=2,
                total_copies=3
            ),
            Book(
                title='Web Development with Django',
                author='William Vincent',
                isbn='9781090751254',
                category='Web Development',
                available_copies=4,
                total_copies=4
            ),
            Book(
                title='Machine Learning: A Probabilistic Perspective',
                author='Kevin P. Murphy',
                isbn='9780262018029',
                category='Machine Learning',
                available_copies=1,
                total_copies=2
            ),
            Book(
                title='Clean Code',
                author='Robert C. Martin',
                isbn='9780132350884',
                category='Software Engineering',
                available_copies=2,
                total_copies=3
            ),
        ]
        
        for book in books:
            db.session.add(book)
        
        db.session.commit()
        print("✅ Books created")
        
        # Create Borrow Records
        borrow_records = [
            BorrowRecord(
                student_id=student.id,
                book_id=1,
                borrow_date=datetime.now() - timedelta(days=10),
                due_date=datetime.now() + timedelta(days=4),
                return_date=None,
                status='Active'
            ),
            BorrowRecord(
                student_id=student.id,
                book_id=3,
                borrow_date=datetime.now() - timedelta(days=5),
                due_date=datetime.now() + timedelta(days=9),
                return_date=None,
                status='Active'
            ),
        ]
        
        for record in borrow_records:
            db.session.add(record)
        
        db.session.commit()
        print("✅ Borrow records created")
        
        print("\n" + "="*50)
        print("🎉 DATABASE SEEDED SUCCESSFULLY!")
        print("="*50)
        print("\n📌 Demo Credentials:")
        print("  Student: student@campus.edu / student123")
        print("  Teacher: teacher@campus.edu / teacher123")
        print("  Admin: admin@campus.edu / admin123")
        print("\n✅ All demo data loaded!")

if __name__ == '__main__':
    seed_database()
