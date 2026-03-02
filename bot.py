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
        try:
            with self.get_connection() as conn:
                conn.execute(
                    "INSERT OR IGNORE INTO users (user_id, username, full_name) VALUES (?, ?, ?)",
            (user_id, username, full_name)
        )
                return True
        except Exception as e:
            print(f"Error registering user: {e}")
            return False

    def get_user(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            return cursor.fetchone()

    def add_schedule(self, class_name, date, time, duration=60, max_participants=15):
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO schedule (class_name, date, time, duration, max_participants) VALUES (?, ?, ?, ?, ?)",
            (class_name, date, time, duration, max_participants)
        )
            conn.commit()

    def get_schedule(self):
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT id, class_name, date, time, duration FROM schedule ORDER BY date, time"
        )
            return cursor.fetchall()

    def book_class(self, user_id, schedule_id):
        try:
            with self.get_connection() as conn:
                # Проверяем, есть ли места
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM bookings WHERE schedule_id = ?",
            (schedule_id,)
        )
                booked_count = cursor.fetchone()[0]

                cursor = conn.execute(
            "SELECT max_participants FROM schedule WHERE id = ?",
            (schedule_id,)
        )
                max_participants = cursor.fetchone()[0]

                if booked_count >= max_participants:
                    return False, "Нет свободных мест"

                # Проверяем остаток занятий у пользователя
                cursor = conn.execute(
            "SELECT remaining_classes FROM users WHERE user_id = ?",
            (user_id,)
        )
                remaining = cursor.fetchone()[0]
                if remaining <= 0:
                    return False, "Недостаточно занятий"

                # Создаём бронирование
                conn.execute(
            "INSERT INTO bookings (user_id, schedule_id) VALUES (?, ?)",
            (user_id, schedule_id)
        )
                # Уменьшаем количество оставшихся занятий
                conn.execute(
            "UPDATE users SET remaining_classes = remaining_classes - 1 WHERE user_id = ?",
            (user_id,)
        )
                conn.commit()
                return True, "Бронирование успешно"
        except sqlite3.IntegrityError:
            return False, "Вы уже записаны на это занятие"
        except Exception as e:
            return False, f"Ошибка: {e}"

    def get_user_bookings(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT s.class_name, s.date, s.time
            FROM bookings b
            JOIN schedule s ON b.schedule_id = s.id
            WHERE b.user_id = ?
            ORDER BY s.date, s.time
        ''', (user_id,))
            return cursor.fetchall()

    def get_remaining_classes(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.execute(
            "SELECT remaining_classes FROM users WHERE user_id = ?",
            (user_id,)
        )
            result = cursor.fetchone()
            return result[0] if result else 0
