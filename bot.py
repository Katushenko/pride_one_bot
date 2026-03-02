from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, Contact
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
        [KeyboardButton("📱 Получить контакт", request_contact=True)],
        [KeyboardButton("👤 Мой профиль"), KeyboardButton("❓ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username
    full_name = user.full_name

    # Проверяем, зарегистрирован ли пользователь
    if db.user_exists(user_id):
        await update.message.reply_text(
            f"Добро пожаловать обратно, {full_name}! Вы уже зарегистрированы.",
            reply_markup=get_mainmenu()
        )
        return

    welcome_text = f"""
👋 Добро пожаловать в бот bothost.ru!

Для регистрации нам нужен ваш номер телефона.

Нажмите кнопку «📱 Получить контакт» ниже, чтобы поделиться номером телефона.
Это безопасно — номер будет использоваться только для связи с вами.

После регистрации вы получите доступ к сервисам bothost.ru
    """

    await update.message.reply_text(welcome_text, reply_markup=get_mainmenu())

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username
    full_name = user.full_name

    contact: Contact = update.message.contact

    if not contact:
        await update.message.reply_text("Не удалось получить контакт. Попробуйте ещё раз.")
        return

    phone_number = contact.phone_number

    # Регистрируем пользователя
    success = db.register_user(user_id, username, full_name, phone_number)

    if success:
        success_text = f"""
✅ Регистрация завершена!

👤 Ваши данные:
ID: {user_id}
Имя: {full_name}
Username: @{username if username else 'не указан'}
Телефон: {phone_number}

Теперь вы можете пользоваться сервисами bothost.ru!

Что вы хотите сделать дальше?
        """
        await update.message.reply_text(success_text, reply_markup=get_mainmenu())
    else:
        await update.message.reply_text("Ошибка при регистрации. Попробуйте позже.")

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = db.get_user(user_id)

    if not user:
        await update.message.reply_text(
            "Вы не зарегистрированы. Используйте /start для регистрации.",
            reply_markup=get_mainmenu()
        )
        return

    profile_text = f"""
👤 Ваш профиль bothost.ru:

🆔 ID: {user[1]}
👤 Имя: {user[3]}
📱 Username: @{user[2] if user[2] else 'не указан'}
📞 Телефон: {user[4]}
🗓️ Зарегистрирован: {user[5].split('.')[0]}
    """
    await update.message.reply_text(profile_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
📖 Помощь по боту bothost.ru

Основные функции:

📱 Регистрация — поделитесь номером телефона для регистрации
👤 Профиль — просмотр ваших данных

Как пользоваться:
1. Нажмите /start
2. Нажмите «📱 Получить контакт» для отправки номера телефона
3. После регистрации вы получите подтверждение

Ваши данные защищены и используются только для сервисов bothost.ru
    """
    await update.message.reply_text(help_text, reply_markup=get_mainmenu())


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "👤 Мой профиль":
        await show_profile(update, context)
    elif text == "❓ Помощь":
        await help_command(update, context)
    else:
        await update.message.reply_text(
            "Используйте кнопки меню для навигации",
            reply_markup=get_mainmenu()
        )

def main():
    # Замените 'YOUR_BOT_TOKEN' на токен вашего бота от @BotFather
    application = Application.builder().token("8668827131:AAEYJSI5zf4p_H7QoqYZGKnFvaRA38ZyLJA").build()

    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Обработчик контактов (когда пользователь отправляет номер телефона)
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact))

    # Обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск бота
    print("Бот bothost.ru запущен...")
    application.run_polling()

if __name__ == '__main__':
    main()
