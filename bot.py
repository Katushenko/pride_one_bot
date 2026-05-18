import logging
from datetime import datetime, date, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import database as db

TOKEN = "8668827131:AAEYJSI5zf4p_H7QoqYZGKnFvaRA38ZyLJA"

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

DAYS_RU = ["Понедельник","Вторник","Среда","Четверг","Пятница","Суббота","Воскресенье"]
MONTHS_RU = ["","Январь","Февраль","Март","Апрель","Май","Июнь","Июль","Август","Сентябрь","Октябрь","Ноябрь","Декабрь"]


def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Расписание",        callback_data="schedule"),
         InlineKeyboardButton("🔍 Свободные занятия", callback_data="available")],
        [InlineKeyboardButton("📝 Мои записи",        callback_data="my_bookings"),
         InlineKeyboardButton("📊 Календарь",         callback_data="calendar")],
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    db.upsert_user(u.id, u.full_name, u.username)
    await update.message.reply_text(
        f"👋 Привет, {u.first_name}!\n\n"
        "🏃 Добро пожаловать в Pride One!\n\n"
        "📅 Расписание занятий\n"
        "✅ Запись на тренировки\n"
        "❌ Отмена записей\n"
        "📊 Календарь посещений\n\n"
        "Выбери действие:",
        reply_markup=main_keyboard()
    )

async def cmd_schedule(update, context):  await _show_schedule(update.message, False)
async def cmd_available(update, context): await _show_available(update.message, update.effective_user.id, False)
async def cmd_bookings(update, context):  await _show_my_bookings(update.message, update.effective_user.id, False)
async def cmd_calendar(update, context):  await _show_calendar(update.message, update.effective_user.id, False)


async def _show_schedule(t, edit):
    classes = db.get_schedule()
    text = "📅 Еженедельное расписание\n\n" if classes else "📅 Расписание пока не добавлено."
    for dow in range(7):
        dc = [c for c in classes if c["day_of_week"] == dow]
        if dc:
            text += f"• {DAYS_RU[dow]}\n"
            for c in dc:
                text += f"  🕐 {c['time']} — {c['name']}\n"
                text += f"     👤 {c['instructor']} · 👥 до {c['max_participants']} чел.\n"
                if c["description"]: text += f"     {c['description']}\n"
            text += "\n"
    mk = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Записаться", callback_data="available")],[InlineKeyboardButton("🏠 Меню", callback_data="main_menu")]])
    if edit: await t.edit_message_text(text, reply_markup=mk)
    else:    await t.reply_text(text, reply_markup=mk)


async def _show_available(t, uid, edit):
    slots = db.get_available_slots(uid, date.today(), 14)
    text = "🔍 Свободные занятия (2 недели)\n\n"
    kb = []
    cur = None
    for s in slots:
        if s["class_date"] != cur:
            cur = s["class_date"]
            d = datetime.strptime(cur, "%Y-%m-%d").date()
            text += f"📆 {d.strftime('%d.%m.%Y')} · {DAYS_RU[d.weekday()]}\n"
        if s["is_booked"]:
            text += f"  ✅ {s['time']} {s['name']} (вы записаны)\n"
        else:
            sp = s["max_participants"] - s["booked_count"]
            if sp > 0:
                text += f"  🟢 {s['time']} {s['name']} · {sp} мест\n"
                kb.append([InlineKeyboardButton(f"➕ {s['class_date']} {s['time']} · {s['name']}", callback_data=f"book|{s['id']}|{s['class_date']}")])
            else:
                text += f"  🔴 {s['time']} {s['name']} (мест нет)\n"
    if not slots: text += "Нет доступных занятий."
    kb.append([InlineKeyboardButton("🏠 Меню", callback_data="main_menu")])
    mk = InlineKeyboardMarkup(kb)
    if edit: await t.edit_message_text(text, reply_markup=mk)
    else:    await t.reply_text(text, reply_markup=mk)


async def _show_my_bookings(t, uid, edit):
    bookings = db.get_active_bookings(uid)
    text = "📝 Мои записи\n\n"
    kb = []
    if not bookings:
        text += "Нет активных записей.\nЗапишитесь на занятие!"
        kb.append([InlineKeyboardButton("🔍 Выбрать занятие", callback_data="available")])
    else:
        for b in bookings:
            d = datetime.strptime(b["class_date"], "%Y-%m-%d").date()
            text += f"📌 {b['name']}\n   {d.strftime('%d.%m.%Y')} ({DAYS_RU[d.weekday()]})\n   {b['time']} · {b['instructor']}\n\n"
            kb.append([InlineKeyboardButton(f"❌ Отменить: {d.strftime('%d.%m')} {b['time']} {b['name']}", callback_data=f"cancel|{b['booking_id']}")])
    kb.append([InlineKeyboardButton("🏠 Меню", callback_data="main_menu")])
    mk = InlineKeyboardMarkup(kb)
    if edit: await t.edit_message_text(text, reply_markup=mk)
    else:    await t.reply_text(text, reply_markup=mk)


async def _show_calendar(t, uid, edit):
    history = db.get_bookings_history(uid)
    today = date.today()
    text = "📊 Календарь посещений\n\n"
    if not history:
        text += "История пуста. Запишитесь на первое занятие!"
    else:
        months = {}
        for b in history:
            d = datetime.strptime(b["class_date"], "%Y-%m-%d").date()
            months.setdefault((d.year, d.month), []).append((d, b))
        for ym in sorted(months, reverse=True):
            y, m = ym
            text += f"{MONTHS_RU[m]} {y}\n"
            for d, b in sorted(months[ym], key=lambda x: x[0]):
                icon = "❌" if b["status"]=="cancelled" else ("🔜" if d>today else "✅")
                text += f"  {icon} {d.strftime('%d.%m')} {b['time']} {b['name']}\n"
            text += "\n"
        vis = sum(1 for b in history if b["status"]=="active" and datetime.strptime(b["class_date"],"%Y-%m-%d").date()<=today)
        upc = sum(1 for b in history if b["status"]=="active" and datetime.strptime(b["class_date"],"%Y-%m-%d").date()>today)
        cnc = sum(1 for b in history if b["status"]=="cancelled")
        text += f"📈 Итого:\n  ✅ Посещено: {vis}\n  🔜 Предстоит: {upc}\n  ❌ Отменено: {cnc}\n"
    mk = InlineKeyboardMarkup([[InlineKeyboardButton("🔍 Записаться", callback_data="available")],[InlineKeyboardButton("🏠 Меню", callback_data="main_menu")]])
    if edit: await t.edit_message_text(text, reply_markup=mk)
    else:    await t.reply_text(text, reply_markup=mk)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = update.effective_user.id
    d = q.data
    if   d == "main_menu":   await q.edit_message_text("🏠 Главное меню\n\nВыбери действие:", reply_markup=main_keyboard())
    elif d == "schedule":    await _show_schedule(q, True)
    elif d == "available":   await _show_available(q, uid, True)
    elif d == "my_bookings": await _show_my_bookings(q, uid, True)
    elif d == "calendar":    await _show_calendar(q, uid, True)
    elif d.startswith("book|"):
        _, cid, cdate = d.split("|")
        await _do_book(q, uid, int(cid), cdate)
    elif d.startswith("cancel|"):
        await _ask_cancel(q, uid, int(d.split("|")[1]))
    elif d.startswith("confirm_cancel|"):
        await _do_cancel(q, uid, int(d.split("|")[1]))


async def _do_book(q, uid, cid, cdate):
    db.upsert_user(q.from_user.id, q.from_user.full_name, q.from_user.username)
    ok, msg = db.book_class(uid, q.from_user.full_name, cid, cdate)
    cls = db.get_class_by_id(cid)
    d = datetime.strptime(cdate, "%Y-%m-%d").date()
    text = (f"✅ Запись подтверждена!\n\n📌 {cls['name']}\n📆 {d.strftime('%d.%m.%Y')} ({DAYS_RU[d.weekday()]})\n⏰ {cls['time']}\n👤 {cls['instructor']}\n\nЖдём вас! 🎉"
            if ok else f"⚠️ Не удалось записаться\n\n{msg}")
    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📝 Мои записи", callback_data="my_bookings")],[InlineKeyboardButton("🔍 Ещё занятия", callback_data="available")]]))


async def _ask_cancel(q, uid, bid):
    b = db.get_booking_by_id(bid, uid)
    if not b: await q.edit_message_text("❌ Запись не найдена."); return
    d = datetime.strptime(b["class_date"], "%Y-%m-%d").date()
    await q.edit_message_text(f"⚠️ Отменить запись?\n\n{b['name']}\n{d.strftime('%d.%m.%Y')} ({DAYS_RU[d.weekday()]})\n{b['time']}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Да, отменить", callback_data=f"confirm_cancel|{bid}")],[InlineKeyboardButton("◀️ Назад", callback_data="my_bookings")]]))


async def _do_cancel(q, uid, bid):
    b = db.get_booking_by_id(bid, uid)
    if not b: await q.edit_message_text("❌ Запись не найдена."); return
    db.cancel_booking(bid, uid)
    d = datetime.strptime(b["class_date"], "%Y-%m-%d").date()
    await q.edit_message_text(f"✅ Запись отменена\n\n{b['name']}\n{d.strftime('%d.%m.%Y')}\n{b['time']}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📝 Мои записи", callback_data="my_bookings")],[InlineKeyboardButton("🏠 Меню", callback_data="main_menu")]]))


def main():
    db.init_db()
    app = Application.builder().token(TOKEN).build()
    for cmd, fn in [("start",start),("schedule",cmd_schedule),("available",cmd_available),("bookings",cmd_bookings),("calendar",cmd_calendar)]:
        app.add_handler(CommandHandler(cmd, fn))
    app.add_handler(CallbackQueryHandler(button_handler))
    logger.info("Pride One Bot started!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()