import sqlite3
import hashlib

def init_db():
    """Initialize the database with a users table"""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  password_hash TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    
    # Create default admin user
    c.execute("SELECT id FROM users WHERE username = ?", ("admin",))
    result = c.fetchone()
    
    if not result:
        # Hash the default password 'password'
        default_password_hash = '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8'  # SHA-256 of 'password'
        c.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                  ("admin", "admin@example.com", default_password_hash))
        conn.commit()
        print("Default admin user created")
    
    conn.close()
    print("Database initialized successfully")

if __name__ == "__main__":
    init_db()