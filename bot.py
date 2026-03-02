import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove, ReplyKeyboardMarkup
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, CallbackQueryHandler, ConversationHandler, ContextTypes
from database import connect, insert_user, get_user_balance, get_booked_classes, get_available_classes, add_booking, reserve_slot, update_user_balance

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

NAME_INPUT, BOOKING_SELECTION = range(2)

def build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
    menu = [buttons[i:i+n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, [header_buttons])
    if footer_buttons:
        menu.append([footer_buttons])
    return menu

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the start command."""
    user_id = update.message.from_user.id
    conn = connect()
    user_name = update.message.from_user.full_name
    insert_user(conn, user_id, user_name)

    reply_markup = ReplyKeyboardMarkup(build_menu(['My Schedule', 'Book a Class', 'My Balance'], n_cols=2), resize_keyboard=True)
    await update.message.reply_text("Welcome! Please select an option:", reply_markup=reply_markup)
    return NAME_INPUT

async def show_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List user's scheduled classes."""
    user_id = update.message.from_user.id
    conn = connect()
    booked_classes = get_booked_classes(conn, user_id)
    if booked_classes:
        response = '\n'.join([
            f"{cls[1]} at {cls[2]}, Type: {cls[3]}"
            for cls in booked_classes
        ])
    else:
        response = "You have no scheduled classes."
    await update.message.reply_text(response)

async def check_balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display the user's remaining class credits."""
    user_id = update.message.from_user.id
    conn = connect()
    balance = get_user_balance(conn, user_id)
    await update.message.reply_text(f"You have {balance} remaining classes.")

async def book_a_class(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Prompt the user to choose a class from the available ones."""
    conn = connect()
    available_classes = get_available_classes(conn)
    if not available_classes:
        await update.message.reply_text("No classes currently available.")
        return ConversationHandler.END

    button_list = []
    for cls in available_classes:
        button_list.append(InlineKeyboardButton(f"{cls[1]} at {cls[2]} ({cls[4]} slots)", callback_data=f'book_{cls[0]}'))

    reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=1))
    await update.message.reply_text("Choose a class to book:", reply_markup=reply_markup)
    return BOOKING_SELECTION

async def confirm_booking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Confirm the booking after selection."""
    query = update.callback_query
    await query.answer()
    _, class_id = query.data.split('_')
    class_id = int(class_id)
    user_id = query.from_user.id
    conn = connect()

    # Check availability
    user_balance = get_user_balance(conn, user_id)
    if user_balance <= 0:
        await query.edit_message_text(text="Insufficient credits. Purchase more classes before booking.")
        return ConversationHandler.END

    # Book the slot
    add_booking(conn, user_id, class_id)
    reserve_slot(conn, class_id)
    update_user_balance(conn, user_id, -1)

    await query.edit_message_text(text=f"Successfully booked class {class_id}. Remaining classes: {user_balance - 1}")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel any ongoing action."""
    await update.message.reply_text("Action canceled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main() -> None:
    """Run the bot."""
    TOKEN = "8668827131:AAEYJSI5zf4p_H7QoqYZGKnFvaRA38ZyLJA"
    application = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("schedule", show_schedule),
            CommandHandler("balance", check_balance),
            CommandHandler("book", book_a_class),
        ],
        states={
            NAME_INPUT: [],
            BOOKING_SELECTION: [CallbackQueryHandler(confirm_booking)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
