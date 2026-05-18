import sqlite3
from datetime import date, timedelta

DB_PATH = "pride_one.db"


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    with _conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id    INTEGER PRIMARY KEY,
                full_name  TEXT,
                username   TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS schedule (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                name             TEXT    NOT NULL,
                instructor       TEXT    NOT NULL,
                day_of_week      INTEGER NOT NULL,
                time             TEXT    NOT NULL,
                duration         INTEGER DEFAULT 60,
                max_participants INTEGER DEFAULT 10,
                description      TEXT,
                is_active        INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS bookings (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL,
                user_name  TEXT,
                class_id   INTEGER NOT NULL,
                class_date TEXT    NOT NULL,
                status     TEXT    DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (class_id) REFERENCES schedule(id),
                UNIQUE (user_id, class_id, class_date)
            );
        """)
        if conn.execute("SELECT COUNT(*) FROM schedule").fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO schedule (name,instructor,day_of_week,time,duration,max_participants,description) VALUES (?,?,?,?,?,?,?)",
                [
                    ("Йога",            "Анна Смирнова",   0, "09:00", 60, 12, "Утренняя йога"),
                    ("Пилатес",         "Мария Иванова",   1, "10:00", 60, 10, "Пилатес для всех"),
                    ("Зумба",           "Карина Петрова",  2, "18:00", 60, 20, "Танцевальная аэробика"),
                    ("Йога",            "Анна Смирнова",   3, "09:00", 60, 12, "Утренняя йога"),
                    ("Силовая",         "Алексей Козлов",  4, "17:00", 90, 15, "Силовые упражнения"),
                    ("Растяжка",        "Мария Иванова",   5, "11:00", 45, 10, "Стретчинг"),
                    ("Воскресная йога", "Анна Смирнова",   6, "10:00", 75, 12, "Йога выходного дня"),
                ],
            )


def upsert_user(user_id, full_name, username):
    with _conn() as conn:
        conn.execute("INSERT OR IGNORE INTO users (user_id,full_name,username) VALUES (?,?,?)", (user_id, full_name, username))


def get_schedule():
    with _conn() as conn:
        return conn.execute("SELECT * FROM schedule WHERE is_active=1 ORDER BY day_of_week,time").fetchall()


def get_class_by_id(class_id):
    with _conn() as conn:
        return conn.execute("SELECT * FROM schedule WHERE id=?", (class_id,)).fetchone()


def get_available_slots(user_id, from_date, days_ahead=14):
    results = []
    with _conn() as conn:
        for i in range(days_ahead):
            d = from_date + timedelta(days=i)
            ds = d.strftime("%Y-%m-%d")
            for c in conn.execute("SELECT * FROM schedule WHERE day_of_week=? AND is_active=1 ORDER BY time", (d.weekday(),)).fetchall():
                booked   = conn.execute("SELECT COUNT(*) FROM bookings WHERE class_id=? AND class_date=? AND status='active'", (c["id"], ds)).fetchone()[0]
                is_booked= conn.execute("SELECT COUNT(*) FROM bookings WHERE user_id=? AND class_id=? AND class_date=? AND status='active'", (user_id, c["id"], ds)).fetchone()[0] > 0
                results.append({"id": c["id"], "name": c["name"], "instructor": c["instructor"], "time": c["time"], "max_participants": c["max_participants"], "class_date": ds, "booked_count": booked, "is_booked": is_booked})
    return results


def book_class(user_id, user_name, class_id, class_date):
    with _conn() as conn:
        c = conn.execute("SELECT * FROM schedule WHERE id=?", (class_id,)).fetchone()
        if not c:
            return False, "Занятие не найдено"
        booked = conn.execute("SELECT COUNT(*) FROM bookings WHERE class_id=? AND class_date=? AND status='active'", (class_id, class_date)).fetchone()[0]
        if booked >= c["max_participants"]:
            return False, "Свободных мест нет"
        try:
            conn.execute("INSERT INTO bookings (user_id,user_name,class_id,class_date) VALUES (?,?,?,?)", (user_id, user_name, class_id, class_date))
            return True, "OK"
        except Exception:
            return False, "Вы уже записаны на это занятие"


def get_active_bookings(user_id):
    today = date.today().strftime("%Y-%m-%d")
    with _conn() as conn:
        return conn.execute("SELECT b.id as booking_id,b.class_date,b.status,s.name,s.time,s.instructor FROM bookings b JOIN schedule s ON b.class_id=s.id WHERE b.user_id=? AND b.status='active' AND b.class_date>=? ORDER BY b.class_date,s.time", (user_id, today)).fetchall()


def get_bookings_history(user_id):
    with _conn() as conn:
        return conn.execute("SELECT b.id as booking_id,b.class_date,b.status,s.name,s.time,s.instructor FROM bookings b JOIN schedule s ON b.class_id=s.id WHERE b.user_id=? ORDER BY b.class_date DESC", (user_id,)).fetchall()


def get_booking_by_id(booking_id, user_id):
    with _conn() as conn:
        return conn.execute("SELECT b.*,s.name,s.time,s.instructor FROM bookings b JOIN schedule s ON b.class_id=s.id WHERE b.id=? AND b.user_id=?", (booking_id, user_id)).fetchone()


def cancel_booking(booking_id, user_id):
    with _conn() as conn:
        conn.execute("UPDATE bookings SET status='cancelled' WHERE id=? AND user_id=?", (booking_id, user_id))