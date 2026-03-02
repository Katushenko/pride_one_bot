import sqlite3
from typing import List, Tuple

def connect():
      conn = sqlite3.connect('fitness.db')
      return conn

def create_tables(conn):
      cursor = conn.cursor()
      cursor.execute('''
          CREATE TABLE IF NOT EXISTS users (
              user_id INTEGER PRIMARY KEY,
              name TEXT NOT NULL,
              remaining_classes INTEGER DEFAULT 10
          )
      ''')
      cursor.execute('''
          CREATE TABLE IF NOT EXISTS schedule (
              class_id INTEGER PRIMARY KEY AUTOINCREMENT,
              date TEXT NOT NULL,
              time TEXT NOT NULL,
              class_type TEXT NOT NULL,
              available_slots INTEGER NOT NULL CHECK (available_slots >= 0)
          )
      ''')
      cursor.execute('''
          CREATE TABLE IF NOT EXISTS bookings (
              booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER NOT NULL,
              class_id INTEGER NOT NULL,
              FOREIGN KEY(user_id) REFERENCES users(user_id),
              FOREIGN KEY(class_id) REFERENCES schedule(class_id)
          )
      ''')
      conn.commit()

def insert_user(conn, user_id: int, name: str):
      cursor = conn.cursor()
      cursor.execute(
          '''
          INSERT INTO users (user_id, name)
          VALUES (?, ?)
          ON CONFLICT(user_id) DO UPDATE SET name=?
          ''',
          (user_id, name, name)
      )
      conn.commit()

def get_user_balance(conn, user_id: int) -> int:
      cursor = conn.cursor()
      result = cursor.execute('SELECT remaining_classes FROM users WHERE user_id=?', (user_id,))
      row = result.fetchone()
      return row[0] if row else 0

def update_user_balance(conn, user_id: int, delta: int):
      cursor = conn.cursor()
      cursor.execute('UPDATE users SET remaining_classes=remaining_classes+? WHERE user_id=?', (delta, user_id))
      conn.commit()

def add_booking(conn, user_id: int, class_id: int):
      cursor = conn.cursor()
      cursor.execute('INSERT INTO bookings (user_id, class_id) VALUES (?, ?)', (user_id, class_id))
      conn.commit()

def get_booked_classes(conn, user_id: int) -> List[Tuple[int, str, str, str]]:
      cursor = conn.cursor()
      result = cursor.execute('''
          SELECT s.class_id, s.date, s.time, s.class_type
          FROM bookings b JOIN schedule s ON b.class_id=s.class_id
          WHERE b.user_id=?
      ''', (user_id,))
      return result.fetchall()

def get_available_classes(conn) -> List[Tuple[int, str, str, str, int]]:
      cursor = conn.cursor()
      result = cursor.execute('SELECT * FROM schedule WHERE available_slots > 0 ORDER BY date ASC, time ASC')
      return result.fetchall()

def reserve_slot(conn, class_id: int):
      cursor = conn.cursor()
      cursor.execute('UPDATE schedule SET available_slots=available_slots-1 WHERE class_id=? AND available_slots > 0', (class_id,))
      conn.commit()

def drop_tables(conn):
      cursor = conn.cursor()
      cursor.execute('DROP TABLE IF EXISTS bookings')
      cursor.execute('DROP TABLE IF EXISTS schedule')
      cursor.execute('DROP TABLE IF EXISTS users')
      conn.commit()
