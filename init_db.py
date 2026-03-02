import random
from datetime import timedelta, datetime
import sqlite3
from database import connect, create_tables, drop_tables

conn = connect()
drop_tables(conn)
create_tables(conn)
cursor = conn.cursor()

# Insert some initial data
sample_data = [
      ('Yoga', 'Monday'),
      ('CrossFit', 'Tuesday'),
      ('Zumba', 'Wednesday'),
      ('Pilates', 'Thursday'),
      ('HIIT', 'Friday'),
]

current_date = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
for i in range(len(sample_data)):
      activity, day = sample_data[i]
      current_date += timedelta(days=(i % 7))    # Ensure different days
      hour = random.randint(8, 19)
      time_str = f'{hour}:00'
      date_str = current_date.strftime('%Y-%m-%d')
      cursor.execute('''INSERT INTO schedule (date, time, class_type, available_slots)
                        VALUES (?, ?, ?, ?)''', (date_str, time_str, activity, random.randint(5, 15)))

conn.commit()
print("Database initialized successfully")
