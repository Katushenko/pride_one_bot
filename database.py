import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_path="bothost_users.db"):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        with self.get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            full_name TEXT,
            phone_number TEXT NOT NULL,
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
            ''')
            conn.commit()

    def register_user(self, telegram_id, username, full_name, phone_number):
        try:
            with self.get_connection() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO users (telegram_id, username, full_name, phone_number) VALUES (?, ?, ?, ?)",
            (telegram_id, username, full_name, phone_number)
        )
                conn.commit()
                return True
        except Exception as e:
            print(f"Error registering user: {e}")
            return False

    def get_user(self, telegram_id):
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
            return cursor.fetchone()

    def user_exists(self, telegram_id):
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT 1 FROM users WHERE telegram_id = ? LIMIT 1", (telegram_id,))
            return cursor.fetchone() is not None
