import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_path="dance_studio.db"):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        with self.get_connection() as conn:
            # Таблица пользователей
            conn.execute('''
                CREATE TABLE IF NOT EXISTS Users (
                    User_Id INTEGER PRIMARY KEY AUTOINCREMENT,
            Telegram_Name TEXT NOT NULL,
            Telegram_Login TEXT,
            Phone_Number TEXT,
            Name TEXT NOT NULL
        )
            ''')

            # Таблица оплаты
            conn.execute('''
                CREATE TABLE IF NOT EXISTS Payment (
            Check_Id INTEGER PRIMARY KEY AUTOINCREMENT,
            User_ID INTEGER NOT NULL,
            BBoy_Id INTEGER NOT NULL,
            Date TEXT NOT NULL,
            Date_Start TEXT NOT NULL,
            Date_End TEXT NOT NULL,
            Count INTEGER NOT NULL,
            Price REAL NOT NULL,
            FOREIGN KEY (User_ID) REFERENCES Users(User_Id),
            FOREIGN KEY (BBoy_Id) REFERENCES BBoy(BBoy_Id)
        )
            ''')

            # Таблица занятий
            conn.execute('''
                CREATE TABLE IF NOT EXISTS Training (
            Training_Id INTEGER PRIMARY KEY AUTOINCREMENT,
            User_ID INTEGER NOT NULL,
            BBoy_Id INTEGER NOT NULL,
            Date TEXT NOT NULL,
            Number INTEGER NOT NULL,
            FOREIGN KEY (User_ID) REFERENCES Users(User_Id),
            FOREIGN KEY (BBoy_Id) REFERENCES BBoy(BBoy_Id)
        )
            ''')

            # Таблица танцоров
            conn.execute('''
                CREATE TABLE IF NOT EXISTS BBoy (
            BBoy_Id INTEGER PRIMARY KEY AUTOINCREMENT,
            User_Id INTEGER NOT NULL,
            Name TEXT NOT NULL,
            FOREIGN KEY (User_Id) REFERENCES Users(User_Id)
        )
            ''')

            # Таблица баланса
            conn.execute('''
                CREATE TABLE IF NOT EXISTS Balance (
            Id INTEGER PRIMARY KEY AUTOINCREMENT,
            User_id INTEGER UNIQUE NOT NULL,
            Balance REAL DEFAULT 0.0,
            FOREIGN KEY (User_id) REFERENCES Users(User_Id)
        )
            ''')
            conn.commit()

    def register_user(self, telegram_name, telegram_login, phone_number, name):
        """Регистрирует нового пользователя"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "INSERT INTO Users (Telegram_Name, Telegram_Login, Phone_Number, Name) VALUES (?, ?, ?, ?)",
            (telegram_name, telegram_login, phone_number, name)
        )
                user_id = cursor.lastrowid

                # Создаём запись в балансе с нулевым балансом
                conn.execute(
            "INSERT OR IGNORE INTO Balance (User_id, Balance) VALUES (?, 0.0)",
            (user_id,)
        )
                conn.commit()
                return user_id
        except Exception as e:
            print(f"Error registering user: {e}")
            return None

    def get_user_by_telegram_name(self, telegram_name):
        """Получает пользователя по Telegram имени"""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM Users WHERE Telegram_Name = ?", (telegram_name,))
            return cursor.fetchone()

    def add_bboy(self, user_id, name):
        """Добавляет танцора"""
        try:
            with self.get_connection() as conn:
                conn.execute(
            "INSERT INTO BBoy (User_Id, Name) VALUES (?, ?)",
            (user_id, name)
        )
                conn.commit()
                return True
        except Exception as e:
            print(f"Error adding bboy: {e}")
            return False

    def add_payment(self, user_id, bboy_id, date, date_start, date_end, count, price):
        """Добавляет запись об оплате"""
        try:
            with self.get_connection() as conn:
                conn.execute(
            "INSERT INTO Payment (User_ID, BBoy_Id, Date, Date_Start, Date_End, Count, Price) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, bboy_id, date, date_start, date_end, count, price)
        )
                conn.commit()
                return True
        except Exception as e:
            print(f"Error adding payment: {e}")
            return False

    def add_training(self, user_id, bboy_id, date, number):
        """Добавляет занятие"""
        try:
            with self.get_connection() as conn:
                conn.execute(
            "INSERT INTO Training (User_ID, BBoy_Id, Date, Number) VALUES (?, ?, ?, ?)",
            (user_id, bboy_id, date, number)
        )
                conn.commit()
                return True
        except Exception as e:
            print(f"Error adding training: {e}")
            return False

    def get_balance(self, user_id):
        """Получает баланс пользователя"""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT Balance FROM Balance WHERE User_id = ?", (user_id,))
            result = cursor.fetchone()
            return result[0] if result else 0.0

    def update_balance(self, user_id, amount):
        """Обновляет баланс пользователя"""
        try:
            with self.get_connection() as conn:
                conn.execute(
            "UPDATE Balance SET Balance = Balance + ? WHERE User_id = ?",
            (amount, user_id)
        )
                conn.commit()
                return True
        except Exception as e:
            print(f"Error updating balance: {e}")
            return False
