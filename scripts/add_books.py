#!/usr/bin/env python3
"""Add demo books to the Campus Connect DB (idempotent).

Run from project root:
    python3 scripts/add_books.py
"""
import sys, os
from datetime import datetime

sys.path.insert(0, os.getcwd())
from app import app, db
from models.library import Book

BOOKS = [
    ("Introduction to Algorithms", "Cormen", "Computer Science", "9780262033848", 5),
    ("Clean Code", "Robert C. Martin", "Software Engineering", "9780132350884", 3),
    ("Operating Systems", "Silberschatz", "Computer Science", "9781118063330", 4),
    ("Database System Concepts", "Korth", "Computer Science", "9780072465631", 3),
    ("Python Crash Course", "Eric Matthes", "Programming", "9781593279288", 6),
]

def main():
    added = 0
    with app.app_context():
        for title, author, category, isbn, copies in BOOKS:
            if Book.query.filter_by(title=title).first():
                print('exists:', title)
                continue
            # `Book` model defines `copies` and `available` fields
            b = Book(title=title, author=author, isbn=isbn, category=category, copies=copies, available=copies)
            db.session.add(b)
            added += 1
        db.session.commit()
    print(f'Done. Books added: {added}')

if __name__ == '__main__':
    main()
