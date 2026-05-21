import sqlite3
from werkzeug.security import generate_password_hash

def get_db():
    conn = sqlite3.connect('spendly.db')
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Create expenses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

def seed_db():
    conn = get_db()
    cursor = conn.cursor()
    # Check if we already have a user
    cursor.execute('SELECT COUNT(*) FROM users')
    count = cursor.fetchone()[0]
    if count > 0:
        conn.close()
        return
    # Create demo user
    password_hash = generate_password_hash('demo123')
    cursor.execute(
        'INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)',
        ('Demo User', 'demo@spendly.com', password_hash)
    )
    user_id = cursor.lastrowid
    # Sample expenses data
    expenses = [
        (user_id, 15.50, 'Food', '2026-05-01', 'Groceries'),
        (user_id, 45.00, 'Transport', '2026-05-02', 'Gas refill'),
        (user_id, 75.00, 'Bills', '2026-05-03', 'Electricity bill'),
        (user_id, 20.00, 'Health', '2026-05-04', 'Pharmacy'),
        (user_id, 30.00, 'Entertainment', '2026-05-05', 'Movie tickets'),
        (user_id, 50.00, 'Shopping', '2026-05-06', 'New clothes'),
        (user_id, 10.00, 'Other', '2026-05-07', 'Donation'),
        (user_id, 120.00, 'Food', '2026-05-08', 'Restaurant dinner'),
    ]
    cursor.executemany(
        'INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)',
        expenses
    )
    conn.commit()
    conn.close()
