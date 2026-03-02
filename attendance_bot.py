from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import sqlite3

# Инициализация бота
API_TOKEN = 'ВАШ_ТОКЕН'  
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Создание базы данных
conn = sqlite3.connect('attendance.db', check_same_thread=False)
cursor = conn.cursor()

# Создание таблицы
cursor.execute('''CREATE TABLE IF NOT EXISTS attendance
             (student_id INTEGER PRIMARY KEY,
              name TEXT,
              lesson1_signup BOOLEAN,
              lesson1_visited BOOLEAN,
              lesson2_signup BOOLEAN,
              lesson2_visited BOOLEAN,
              lesson3_signup BOOLEAN,
              lesson3_visited BOOLEAN)''')
conn.commit()
