-- CampusConnect Complete Schema
-- Run this to create/update all tables

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'student',  -- 'teacher' | 'student' | 'admin'
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    name TEXT NOT NULL,
    email TEXT,
    roll_no TEXT UNIQUE,
    branch TEXT,
    semester INTEGER DEFAULT 1,
    cgpa REAL DEFAULT 0.0,
    phone TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    subject TEXT NOT NULL,
    description TEXT,
    due_date TEXT NOT NULL,
    status TEXT DEFAULT 'Pending',   -- 'Pending' | 'Submitted'
    teacher_id INTEGER REFERENCES users(id),
    student_id INTEGER REFERENCES students(id),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER REFERENCES students(id),
    subject TEXT NOT NULL,
    internal REAL DEFAULT 0,
    external REAL DEFAULT 0,
    grade TEXT,
    semester INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER REFERENCES students(id),
    teacher_id INTEGER REFERENCES users(id),
    subject TEXT NOT NULL,
    date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Absent',  -- 'Present' | 'Absent'
    UNIQUE(student_id, subject, date)
);

CREATE TABLE IF NOT EXISTS notices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    priority TEXT DEFAULT 'Normal',   -- 'Normal' | 'Important' | 'Urgent'
    teacher_id INTEGER REFERENCES users(id),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER REFERENCES users(id),
    receiver_id INTEGER REFERENCES users(id),
    content TEXT NOT NULL,
    is_read INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Sample seed data
INSERT OR IGNORE INTO users (id, name, email, password, role) VALUES
(1, 'ayush', 'shubhamsing615@gmail.com', 'hashed_pass', 'teacher'),
(2, 'Alice Johnson', 'alice@student.com', 'hashed_pass', 'student'),
(3, 'Bob Smith', 'bob@student.com', 'hashed_pass', 'student');

INSERT OR IGNORE INTO students (user_id, name, email, roll_no, branch, semester, cgpa, phone) VALUES
(2, 'Alice Johnson', 'alice@student.com', 'CS2021001', 'Computer Science', 5, 8.7, '9876543210'),
(3, 'Bob Smith', 'bob@student.com', 'CS2021002', 'Computer Science', 5, 7.9, '9876543211');
