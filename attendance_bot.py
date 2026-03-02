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

class StudentRegistration(StatesGroup):
    name = State()

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await StudentRegistration.name.set()
    await message.answer("Введите ваше имя:")

@dp.message_handler(state=StudentRegistration.name)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
        
    cursor.execute("INSERT INTO attendance (name) VALUES (?)", (data['name'],))
    conn.commit()
    await state.finish()
    await message.answer("Вы зарегистрированы!")

@dp.message_handler(commands=['signup'])
async def signup(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Занятие 1", "Занятие 2", "Занятие 3")
    await message.answer("Выберите занятие для записи:", reply_markup=keyboard)

@dp.message_handler(lambda message: message.text in ["Занятие 1", "Занятие 2", "Занятие 3"])
async def mark_attendance(message: types.Message):
    lesson = message.text
    # Логика отметки присутствия
    await message.answer(f"Вы записаны на {lesson}")
