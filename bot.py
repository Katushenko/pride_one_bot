from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from envparse import env
from database import register_user, db_session, User

# Загружаем переменную окружения
env.read_envfile('.env')
TOKEN = env.str('BOT_TOKEN')

dp = Dispatcher()

class RegistrationForm(StatesGroup):
    fullname = State()
    email = State()

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    """
    Начальное состояние. Спрашиваем полное имя пользователя.
    """
    await message.answer("Здравствуйте! Давайте начнём регистрацию.\nВведите ваше полное имя:")
    await state.set_state(RegistrationForm.fullname)

@dp.message(RegistrationForm.fullname)
async def process_fullname(message: types.Message, state: FSMContext):
    """
    Сохраняем полное имя и запрашиваем адрес электронной почты.
    """
    await state.update_data(fullname=message.text.strip())
    await message.answer("Спасибо!\nТеперь введите вашу электронную почту:")
    await state.set_state(RegistrationForm.email)

@dp.message(RegistrationForm.email)
async def process_email(message: types.Message, state: FSMContext):
    """
    Завершаем регистрацию и сохраняем данные в базу.
    """
    email = message.text.strip()
    data = await state.get_data()
    fullname = data['fullname']

    # Регистрируем пользователя
    user = register_user(fullname, email)
    await message.answer(f"Пользователь зарегистрирован: Имя - {fullname}, Email - {email}", reply_markup=get_main_menu())

    await state.clear()

def get_main_menu():
    """
    Возвращает главное меню клавиатуры.
    """
    kb = [[KeyboardButton(text="/start")]]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    return keyboard

if __name__ == '__main__':
    bot = Bot(8668827131:AAEYJSI5zf4p_H7QoqYZGKnFvaRA38ZyLJA)
    dp.run_polling(bot)
