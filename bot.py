import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

BOT_TOKEN = "8539264650:AAGzgTQNH0DeqxsRMruQEBEXVXtj5x-mJqQ"
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def get_db():
    return sqlite3.connect('school.db')

def get_schedule_text(name, mode="class"):
    conn = get_db()
    cur = conn.cursor()
    query = "SELECT day, lesson_num, subject, room FROM schedule WHERE class_name=? ORDER BY day, lesson_num" if mode == "class" else "SELECT day, lesson_num, subject, room FROM schedule WHERE teacher_name=? ORDER BY day, lesson_num"
    cur.execute(query, (name,))
    data = cur.fetchall()
    
    if not data:
        return f"Расписание для {name} пока не заполнено."
    
    text = f"📅 Расписание: {name}\n"
    current_day = ""
    for row in data:
        if row[0] != current_day:
            text += f"\n📌 <b>{row[0]}</b>:\n"
            current_day = row[0]
        text += f"{row[1]}. {row[2]} ({row[3]})\n"
    return text

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def start(message: types.Message):
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="📅 Расписание", callback_data="main_sched"))
    kb.row(types.InlineKeyboardButton(text="⭐ Избранное", callback_data="main_favs"))
    await message.answer("Выберите действие:", reply_markup=kb.as_markup())

@dp.callback_query(F.data == "main_sched")
async def select_type(callback: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.add(types.InlineKeyboardButton(text="Для классов", callback_data="type_class"))
    kb.add(types.InlineKeyboardButton(text="Для учителей", callback_data="type_teacher"))
    await callback.message.edit_text("Чье расписание смотрим?", reply_markup=kb.as_markup())

@dp.callback_query(F.data == "type_class")
async def list_classes(callback: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    # Генерируем сетку 5-11 классы
    for grade in range(5, 12):
        row = []
        letters = ["А", "Б", "В"] if grade < 10 else ["А", "Б"]
        for letter in letters:
            name = f"{grade}{letter}"
            row.append(types.InlineKeyboardButton(text=name, callback_data=f"show_class_{name}"))
        kb.row(*row)
    kb.row(types.InlineKeyboardButton(text="⬅ Назад", callback_data="main_sched"))
    await callback.message.edit_text("Выберите класс:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("show_"))
async def show_sched(callback: types.CallbackQuery):
    _, mode, name = callback.data.split("_")
    text = get_schedule_text(name, mode)
    
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="⭐ В избранное", callback_data=f"addfav_{name}"))
    kb.row(types.InlineKeyboardButton(text="⬅ Назад", callback_data=f"type_{mode}"))
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("addfav_"))
async def add_favorite(callback: types.CallbackQuery):
    name = callback.data.split("_")[1]
    user_id = callback.from_user.id
    
    conn = get_db()
    cur = conn.cursor()
    # Проверяем, нет ли уже в избранном
    cur.execute("SELECT * FROM favorites WHERE user_id=? AND class_name=?", (user_id, name))
    if not cur.fetchone():
        cur.execute("INSERT INTO favorites (user_id, class_name) VALUES (?, ?)", (user_id, name))
        conn.commit()
        await callback.answer(f"{name} добавлен в избранное!")
    else:
        await callback.answer("Уже в избранном")
    conn.close()

@dp.callback_query(F.data == "main_favs")
async def show_favorites(callback: types.CallbackQuery):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT class_name FROM favorites WHERE user_id=?", (callback.from_user.id,))
    favs = cur.fetchall()
    
    if not favs:
        await callback.answer("У вас нет избранного", show_alert=True)
        return

    kb = InlineKeyboardBuilder()
    for f in favs:
        kb.add(types.InlineKeyboardButton(text=f[0], callback_data=f"show_class_{f[0]}"))
    kb.row(types.InlineKeyboardButton(text="⬅ Назад", callback_data="start_back"))
    
    await callback.message.edit_text("Ваше избранное:", reply_markup=kb.as_markup())

@dp.callback_query(F.data == "start_back")
async def back_to_start(callback: types.CallbackQuery):
    await start(callback.message)

# --- ЛОГИКА УВЕДОМЛЕНИЙ ---
async def notify_updates(target_name):
    """
    Эту функцию нужно вызвать, когда админка меняет расписание для target_name.
    """
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM favorites WHERE class_name=?", (target_name,))
    users = cur.fetchall()
    
    for user in users:
        try:
            await bot.send_message(user[0], f"🔔 Внимание! Расписание для {target_name} изменилось.")
        except:
            pass # Пользователь мог заблокировать бота
    conn.close()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())