from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from database import Database
import logging

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация базы данных
db = Database()

# Клавиатура главного меню
def get_main_menu():
    keyboard = [
        [KeyboardButton("📋 Расписание"), KeyboardButton("🎟️ Забронировать")],
        [KeyboardButton("👤 Мой профиль"), KeyboardButton("❓ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username
    full_name = user.full_name

    # Регистрируем пользователя
    db.register_user(user_id, username, full_name)

    welcome_text = f"""
Добро пожаловать, {full_name}! 👋

Я бот для записи на занятия. Вот что я умею:

📋 Расписание — посмотреть доступные занятия
🎟️ Забронировать — записаться на занятие
👤 Мой профиль — информация о ваших занятиях
❓ Помощь — справка по боту

У вас {db.get_remaining_classes(user_id)} оставшихся занятий.
    """


    await update.message.reply_text(welcome_text, reply_markup=get_mainmenu())

async def show_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    schedule = db.get_schedule()
    if not schedule:
        await update.message.reply_text("Расписание пока пустое. Скоро будут добавлены новые занятия!")
        return

    schedule_text = "📅 Доступные занятия:\n\n"
    for class_id, name, date, time, duration in schedule:
        schedule_text += f"📌 {name}\n🗓️ {date}\n⏰ {time}\n⏱️ {duration} мин\nID: {class_id}\n\n"

    await update.message.reply_text(schedule_text)

async def book_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Введите ID занятия для бронирования (можно посмотреть в расписании):"
    )
    context.user_data['await
