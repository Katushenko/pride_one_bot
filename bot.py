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

# ID администратора (замените на ваш Telegram ID)
ADMIN_IDS = [298909647]  # Замените на реальный ID

# Состояние пользователя
USER_STATES = {}

# Клавиатура главного меню
def get_main_menu():
    keyboard = [
        [KeyboardButton("💰 Баланс")],
        [KeyboardButton("👤 Мой профиль")]
    ]
    if USER_STATES.get(update.effective_user.id) in ['admin']:
        keyboard.append([KeyboardButton("➕ Добавить танцора"), KeyboardButton("➕ Добавить оплату")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    telegram_name = user.full_name
    telegram_login = user.username

    user_id = user.id

    # Проверяем, зарегистрирован ли пользователь
    existing_user = db.get_user_by_telegram_name(telegram_name)
    if existing_user:
        await update.message.reply_text(
            f"Добро пожаловать обратно, {existing_user[4]}!",
            reply_markup=get_mainmenu()
        )
        return

    # Запрос имени для регистрации
    USER_STATES[user_id] = 'waiting_for_name'
    await update.message.reply_text(
        "Добро пожаловать! Для регистрации введите ваше имя:"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text


    # Обработка состояния ожидания имени
    if USER_STATES.get(user_id) == 'waiting_for_name':
        name = text.strip()
        telegram_name = update.effective_user.full_name
        telegram_login = update.effective_user.username
        phone_number = None  # Можно добавить запрос номера телефона

        user_id_db = db.register_user(telegram_name, telegram_login, phone_number, name)

        if user_id_db:
            USER_STATES[user_id] = None
            await update.message.reply_text(
                f"✅ Регистрация завершена! Добро пожаловать, {name}!",
                reply_markup=get_main_menu()
            )
        else:
            await update.message.reply_text("❌ Ошибка при регистрации. Попробуйте ещё раз.")
        return

    # Обработка команд меню
    if text == "💰 Баланс":
        balance = db.get_balance(user_id)
        await update.message.reply_text(f"💰 Ваш баланс: {balance} руб.")

    elif text == "👤 Мой профиль":
        user = db.get_user_by_telegram_name(update.effective_user.full_name)
        if user:
            profile_text = f"""
👤 Ваш профиль:

ID: {user[0]}
Имя: {user[4]}
Telegram: {user[1]}
Логин: @{user[2] if user[2] else 'не указан'}
Телефон: {user[3] if user[3] else 'не указан'}
            """
            await update.message.reply_text(profile_text)
        else:
            await update.message.reply_text("❌ Пользователь не найден.")

    # Административные команды
    elif user_id in ADMIN_IDS:
        if text == "➕ Добавить танцора":
            USER_STATES[user_id] = 'waiting_bboy_name'
            await update.message.reply_text("Введите имя танцора:")

        elif text == "➕ Добавить оплату":
            USER_STATES[user_id] = 'waiting_payment_data'
            await update.message.reply_text(
                "Введите данные оплаты в формате:\n"
                "User_ID, BBoy_Id, Дата, Дата_начала, Дата_окончания, Количество, Цена\n\n"
                "Пример:\n1, 1, 2024-03-15, 2024-03-15 18:00, 2024-03-15 19:00, 1, 1500"
            )

    else:
        await update.message.reply_text(
            "Используйте кнопки меню для навигации",
            reply_markup=get_main_menu()
        )


async def handle_admin_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS:
        return

    state = USER_STATES.get(user_id)
    text = update.message.text.strip()

    if state == 'waiting_bboy_name':
        # Добавляем танцора
        success = db.add_bboy(user_id, text)
        if success:
            await update.message.reply_text("✅ Танцор успешно добавлен!")
        else:
            await update.message.reply_text("❌ Ошибка при добавлении танцора.")
        USER_STATES[user_id] = None

    elif state == 'waiting_payment_data':
        try:
            # Парсим данные оплаты
            data = [x.strip() for x in text.split(',')]
            if len(data) != 7:
                raise ValueError("Неверное количество параметров")

            user_id_payment = int(data[0])
            bboy_id = int(data[1])
            date = data[2]
            date_start = data[3]
            date_end = data[4]
            count = int(data[5])
            price = float(data[6])

            success = db.add_payment(user_id_payment, bboy_id, date, date_start, date_end, count, price)
            if success:
                # Обновляем баланс пользователя
                db.update_balance(user_id_payment, price)
                await update.message.reply_text("✅ Оплата успешно добавлена и баланс обновлён!")
            else:
                await update.message.reply_text("❌ Ошибка при добавлении оплаты.")
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка формата данных: {e}")
        USER_STATES[user_id] = None

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
📖 Помощь по боту танцевальной студии

Основные функции:

💰 Баланс — просмотр вашего баланса
👤 Мой профиль — просмотр ваших данных

Для администраторов:
➕ Добавить танцора — добавление нового танцора
➕ Добавить оплату — добавление записи об оплате

Используйте кнопки меню для навигации!
    """
    await update.message.reply_text(help_text, reply_markup=get_main_menu())


def main():
    # Замените 'YOUR_BOT_TOKEN' на токен вашего бота от @BotFather
    application = Application.builder().token("8668827131:AAEYJSI5zf4p_H7QoqYZGKnFvaRA38ZyLJA").build()

    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск бота
    print("Бот танцевальной студии запущен...")
    application.run_polling()

if __name__ == '__main__':
    main()
