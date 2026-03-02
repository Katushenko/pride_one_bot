import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_path="classes.db"):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        with self.get_connection() as conn:
            # Таблица пользователей
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
            user_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            full_name TEXT,
            remaining_classes INTEGER DEFAULT 10,
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
            ''')

            # Таблица расписания занятий
            conn.execute('''
                CREATE TABLE IF NOT EXISTS schedule (
            id INTEGER PRIMARY KEY,
            class_name TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            duration INTEGER DEFAULT 60,
            max_participants INTEGER DEFAULT 15
        )
            ''')

            # Таблица бронирований
            conn.execute('''
                CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            schedule_id INTEGER NOT NULL,
            booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (schedule_id) REFERENCES schedule (id),
            UNIQUE(user_id, schedule_id)
        )
            ''')
            conn.commit()

    def register_user(self, user_id, username, full_name):
