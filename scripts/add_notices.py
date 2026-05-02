#!/usr/bin/env python3
"""Add demo notices, events and a sample assignment to the Campus Connect DB (idempotent).

This script is safe to run multiple times. It inserts items only when a
matching title doesn't already exist.

Run from project root:
    python3 scripts/add_notices.py
"""
import sys
import os
from datetime import datetime, timedelta

# Ensure the project root is importable so `from app import app, db` works
sys.path.insert(0, os.getcwd())

from app import app, db
from models.notice import Notice, Event
try:
    # Assignment/Student models may exist in student module
    from models.student import Assignment, Student
except Exception:
    Assignment = None
    Student = None

NOTICES = [
    ("Mid-Sem Exam: Room Allocation",
     "Rooms for mid-sem exams have been allocated. Check your department noticeboard for details.",
     "Exams", "Exam Cell"),

    ("Guest Lecture: Cloud Native Apps",
     "Join us for a guest lecture on cloud-native architectures by an industry expert.",
     "Seminar", "CS Dept"),

    ("Library: New Arrivals",
     "New textbooks and reference books have arrived. Visit the library to borrow.",
     "General", "Library"),

    ("Scholarship Information Session",
     "An information session about new scholarships for meritorious students. Register at the placement cell.",
     "Placement", "Placement Cell"),

    ("Cultural Fest: VIBE 2026",
     "VIBE 2026 registrations open for dance, music, drama and art competitions!",
     "Events", "Student Council"),
]

EVENTS = [
    ("Annual Tech Fest 2026", "3-day tech festival with coding competitions and hackathons", date := (datetime.now() + timedelta(days=20)).date()),
    ("Sports Day 2026", "Inter-class sports competitions", (datetime.now() + timedelta(days=30)).date()),
    ("Guest Lecture: AI in Industry", "Industry expert talk on applications of AI", (datetime.now() + timedelta(days=15)).date()),
]

ASSIGNMENTS = [
    ("Data Structures Assignment 1", "Data Structures", 10),
    ("Database Systems Mini Project", "Database Systems", 14),
]

def main():
    added_notices = 0
    added_events = 0
    added_assignments = 0

    with app.app_context():
        for title, content, category, posted_by in NOTICES:
            if Notice.query.filter_by(title=title).first():
                print(f"notice exists: {title}")
                continue
            n = Notice(title=title, content=content, category=category, posted_by=posted_by, date=datetime.now() - timedelta(days=1))
            db.session.add(n)
            added_notices += 1

        for title, desc, edate in EVENTS:
            if Event.query.filter_by(title=title).first():
                print(f"event exists: {title}")
                continue
            e = Event(title=title, description=desc, event_date=edate, category='General')
            db.session.add(e)
            added_events += 1

        # Add a couple of assignments if models exist and at least one student exists
        if Assignment is not None and Student is not None:
            first_student = Student.query.first()
            if first_student:
                for title, subject, days in ASSIGNMENTS:
                    exists = Assignment.query.filter_by(title=title, student_id=first_student.id).first()
                    if exists:
                        print(f"assignment exists for student {first_student.id}: {title}")
                        continue
                    a = Assignment(student_id=first_student.id, title=title, subject=subject,
                                   due_date=datetime.now() + timedelta(days=days), status='Pending')
                    db.session.add(a)
                    added_assignments += 1
            else:
                print("no student found: skipping assignment creation")
        else:
            print("Assignment or Student model not found — skipping assignments")

        db.session.commit()

    print(f"Done. Notices added: {added_notices}, Events added: {added_events}, Assignments added: {added_assignments}")


if __name__ == '__main__':
    main()
