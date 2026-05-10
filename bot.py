import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- КОНФИГУРАЦИЯ ---
BOT_TOKEN = "8539264650:AAGzgTQNH0DeqxsRMruQEBEXVXtj5x-mJqQ"
DB_FILE = "data/school_db.json"
FAVS_FILE = "data/favorites.json"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- ФУНКЦИИ ДАННЫХ ---

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {"schedule": {}}
    return {"schedule": {}}

def load_favs():
    if os.path.exists(FAVS_FILE):
        try:
            with open(FAVS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}
    return {}

def save_favs(data):
    os.makedirs("data", exist_ok=True)
    with open(FAVS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_schedule_text(name, mode="class"):
    db = load_db()
    sc = db.get("schedule", {})
    data = {}
    if mode == "class":
        data = sc.get(name, {})
    else:
        for c_name, days in sc.items():
            for day, lessons in days.items():
                if day not in data: data[day] = {}
                for num, info in lessons.items():
                    if info.get('t') == name:
                        data[day][num] = {"s": info['s'], "r": f"{info['r']} ({c_name})"}
    
    if not data: return f"❌ Расписание для <b>{name}</b> не найдено."

    text = f"📅 <b>Расписание: {name}</b>\n"
    for day in ["Пн", "Вт", "Ср", "Чт", "Пт"]:
        if day in data and data[day]:
            text += f"\n📌 <b>{day}:</b>\n"
            for num in sorted(data[day].keys(), key=int):
                item = data[day][num]
                text += f"{num}. {item['s']} — {item['r']}\n"
    return text

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="👥 Классы", callback_data="list_classes"))
    kb.row(types.InlineKeyboardButton(text="👨‍🏫 Учителя", callback_data="list_teachers"))
    kb.row(types.InlineKeyboardButton(text="⭐ Моё избранное", callback_data="show_favs"))
    await message.answer("Выберите раздел:", reply_markup=kb.as_markup())

@dp.callback_query(F.data == "list_classes")
async def list_classes(callback: types.CallbackQuery):
    db = load_db()
    classes = sorted(list(db.get("schedule", {}).keys()))
    if not classes:
        await callback.answer("База пуста", show_alert=True)
        return
    kb = InlineKeyboardBuilder()
    for c in classes:
        kb.add(types.InlineKeyboardButton(text=c, callback_data=f"view_c_{c}"))
    kb.adjust(3)
    kb.row(types.InlineKeyboardButton(text="⬅ Назад", callback_data="to_start"))
    await callback.message.edit_text("Выберите класс:", reply_markup=kb.as_markup())

@dp.callback_query(F.data == "list_teachers")
async def list_teachers(callback: types.CallbackQuery):
    db = load_db()
    teachers = set()
    for days in db.get("schedule", {}).values():
        for lessons in days.values():
            for info in lessons.values():
                if info.get('t'): teachers.add(info['t'])
    if not teachers:
        await callback.answer("Учителя не найдены", show_alert=True)
        return
    kb = InlineKeyboardBuilder()
    for t in sorted(list(teachers)):
        kb.add(types.InlineKeyboardButton(text=t, callback_data=f"view_t_{t}"))
    kb.adjust(2)
    kb.row(types.InlineKeyboardButton(text="⬅ Назад", callback_data="to_start"))
    await callback.message.edit_text("Выберите учителя:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("view_"))
async def view_item(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    mode_char = parts[1]
    name = "_".join(parts[2:])
    user_id = str(callback.from_user.id)
    
    mode = "class" if mode_char == "c" else "teacher"
    text = get_schedule_text(name, mode)
    
    # Проверяем, есть ли уже в избранном
    favs = load_favs().get(user_id, {"c": [], "t": []})
    is_fav = name in (favs["c"] if mode_char == "c" else favs["t"])
    
    kb = InlineKeyboardBuilder()
    if is_fav:
        kb.row(types.InlineKeyboardButton(text="❌ Удалить из избранного", callback_data=f"remfav_{mode_char}_{name}"))
    else:
        kb.row(types.InlineKeyboardButton(text="⭐ В избранное", callback_data=f"addfav_{mode_char}_{name}"))
    
    kb.row(types.InlineKeyboardButton(text="⬅ Назад", callback_data="to_start"))
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("addfav_"))
async def add_to_fav(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    mode_char, name = parts[1], "_".join(parts[2:])
    user_id = str(callback.from_user.id)
    favs = load_favs()
    if user_id not in favs: favs[user_id] = {"c": [], "t": []}
    
    target = favs[user_id]["c"] if mode_char == "c" else favs[user_id]["t"]
    if name not in target:
        target.append(name)
        save_favs(favs)
        await callback.answer(f"✅ {name} в избранном")
        # Обновляем сообщение, чтобы кнопка сменилась на "Удалить"
        await view_item(callback)

@dp.callback_query(F.data.startswith("remfav_"))
async def rem_from_fav(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    mode_char, name = parts[1], "_".join(parts[2:])
    user_id = str(callback.from_user.id)
    favs = load_favs()
    
    if user_id in favs:
        target = favs[user_id]["c"] if mode_char == "c" else favs[user_id]["t"]
        if name in target:
            target.remove(name)
            save_favs(favs)
            await callback.answer(f"🗑 {name} удален")
            # Обновляем сообщение, чтобы кнопка сменилась на "Добавить"
            await view_item(callback)

@dp.callback_query(F.data == "show_favs")
async def show_favs(callback: types.CallbackQuery):
    user_id = str(callback.from_user.id)
    favs = load_favs().get(user_id, {"c": [], "t": []})
    if not favs["c"] and not favs["t"]:
        await callback.answer("Избранное пусто", show_alert=True)
        return
    kb = InlineKeyboardBuilder()
    for c in favs["c"]: kb.row(types.InlineKeyboardButton(text=f"👥 {c}", callback_data=f"view_c_{c}"))
    for t in favs["t"]: kb.row(types.InlineKeyboardButton(text=f"👨‍🏫 {t}", callback_data=f"view_t_{t}"))
    kb.row(types.InlineKeyboardButton(text="⬅ Назад", callback_data="to_start"))
    await callback.message.edit_text("Ваше избранное:", reply_markup=kb.as_markup())

@dp.callback_query(F.data == "to_start")
async def to_start(callback: types.CallbackQuery):
    await cmd_start(callback.message)
    await callback.answer()

async def check_updates_task():
    last_mtime = os.path.getmtime(DB_FILE) if os.path.exists(DB_FILE) else 0
    while True:
        await asyncio.sleep(15)
        if os.path.exists(DB_FILE):
            curr = os.path.getmtime(DB_FILE)
            if curr > last_mtime:
                last_mtime = curr
                await send_notifications()

async def send_notifications():
    favs = load_favs()
    for uid in favs:
        try:
            await bot.send_message(uid, "🔔 Расписание обновлено!")
        except: pass

async def main():
    asyncio.create_task(check_updates_task())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())