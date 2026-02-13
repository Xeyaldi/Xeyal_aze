import asyncio
import sqlite3
import logging
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

# ==========================================================
# ⚙️ KONFİQURASİYA
# ==========================================================

OWNER_ID = 8024893255
API_TOKEN = "7886882115:AAEodWPGRhT6CQ-1rQgHy4ZKL_3wkKENe8Q"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# ==========================================================
# 📊 MƏLUMAT BAZASI SİSTEMİ
# ==========================================================

def init_db():
    connection = sqlite3.connect("flower_security_ultra.db")
    cursor = connection.cursor()
    # Kateqoriyalar artıq birbaşa Azərbaycan dilində saxlanılır
    cursor.execute('''CREATE TABLE IF NOT EXISTS scores (chat_id INTEGER, user_id INTEGER, kateqoriya TEXT, msg_sayi INTEGER DEFAULT 0, stiker_sayi INTEGER DEFAULT 0, gif_sayi INTEGER DEFAULT 0, PRIMARY KEY (chat_id, user_id, kateqoriya))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_info (user_id INTEGER PRIMARY KEY, first_name TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings (chat_id INTEGER PRIMARY KEY, stiker_bloku INTEGER DEFAULT 0)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS warns (chat_id INTEGER, user_id INTEGER, say INTEGER DEFAULT 0, PRIMARY KEY (chat_id, user_id))''')
    connection.commit()
    return connection, cursor

db_conn, db_cursor = init_db()

# ==========================================================
# 🛡️ ADMİN YOXLANIŞI
# ==========================================================

async def is_admin(chat_id: int, user_id: int):
    if user_id == OWNER_ID: return True
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ("administrator", "creator")
    except: return False

def vaxt_hesabla(vaxt_str: str):
    try:
        miqdar = int(vaxt_str[:-1])
        vahid = vaxt_str[-1].lower()
        if vahid == "m": return timedelta(minutes=miqdar)
        if vahid == "h": return timedelta(hours=miqdar)
        if vahid == "d": return timedelta(days=miqdar)
        return None
    except: return None

# ==========================================================
# 👋 START VƏ BÜTÜN DÜYMƏLƏR
# ==========================================================

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    welcome_text = (
        f"👋 Salam {message.from_user.first_name}!\n\n"
        f"🌸 Flower Security botuna xoş gəldiniz.\n"
        f"🛡️ Mən qrupları qorumaq və reytinqi hesablamaq üçün yaradılmışam.\n\n"
        f"⚙️ Ayarlar (Kurucu):\n"
        f"/stiker on|off, /setrules, /setwarn, /panel\n\n"
        f"🌐 Federasiya:\n"
        f"/newfed, /joinfed, /fban\n\n"
        f"🎲 Əyləncə: /dice\n\n"
        f"🚀 Məni qrupunuza əlavə edib admin edərək işlədə bilərsiniz.\n"
        f"ℹ️ Daha çox məlumat üçün /help yazın."
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="➕ Məni Qrupa Əlavə Et", url=f"https://t.me/Miss_Flower_bot?startgroup=true"))
    builder.row(
        InlineKeyboardButton(text="🛡️ Federasiya", callback_data="fed_info"),
        InlineKeyboardButton(text="⚙️ Ayarlar", callback_data="settings_info")
    )
    builder.row(InlineKeyboardButton(text="🇦🇿 Rəsmi Kanal", url="https://t.me/Aysberq_HT"))
    
    await message.answer(welcome_text, reply_markup=builder.as_markup())

# ==========================================================
# 👮 ADMİN KOMANDALARI (MUTE, WARN, UNWARN)
# ==========================================================

@dp.message(Command("mute"))
async def mute_handler(message: types.Message, command: CommandObject):
    if message.chat.type == "private" or not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return await message.answer("⚠️ Səssizə almaq üçün istifadəçini cavablayın.")
    
    duration = vaxt_hesabla(command.args) if command.args else None
    until = datetime.now() + duration if duration else None
    try:
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, permissions=types.ChatPermissions(can_send_messages=False), until_date=until)
        await message.answer(f"🔇 {message.reply_to_message.from_user.first_name} səssizə alındı.")
    except: pass

@dp.message(Command("warn"))
async def warn_handler(message: types.Message):
    if message.chat.type == "private" or not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    u_id, c_id = message.reply_to_message.from_user.id, message.chat.id
    db_cursor.execute("INSERT OR IGNORE INTO warns VALUES (?, ?, 0)", (c_id, u_id))
    db_cursor.execute("UPDATE warns SET say = say + 1 WHERE chat_id = ? AND user_id = ?", (c_id, u_id))
    db_conn.commit()
    db_cursor.execute("SELECT say FROM warns WHERE chat_id = ? AND user_id = ?", (c_id, u_id))
    cnt = db_cursor.fetchone()[0]
    if cnt >= 3:
        await bot.ban_chat_member(c_id, u_id)
        db_cursor.execute("UPDATE warns SET say = 0 WHERE chat_id = ? AND user_id = ?", (c_id, u_id))
        db_conn.commit()
        await message.answer(f"🚫 {message.reply_to_message.from_user.first_name} 3 xəbərdarlığa görə qovuldu.")
    else: await message.answer(f"⚠️ {message.reply_to_message.from_user.first_name} xəbərdarlıq aldı: {cnt}/3")

@dp.message(Command("unwarn"))
async def unwarn_handler(message: types.Message):
    if message.chat.type == "private" or not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    db_cursor.execute("UPDATE warns SET say = 0 WHERE chat_id = ? AND user_id = ?", (message.chat.id, message.reply_to_message.from_user.id))
    db_conn.commit()
    await message.answer(f"✅ {message.reply_to_message.from_user.first_name} xəbərdarlıqları təmizləndi.")

# ==========================================================
# 📊 REYTİNQ (TAM AZƏRBAYCAN DİLİNDƏ)
# ==========================================================

def get_reytinq_menyusu():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📅 Günlük", callback_data="top_günlük"), InlineKeyboardButton(text="📅 Həftəlik", callback_data="top_həftəlik"), InlineKeyboardButton(text="📅 Aylıq", callback_data="top_aylıq"))
    builder.row(InlineKeyboardButton(text="📊 Ümumi Reytinq", callback_data="top_ümumi"))
    return builder.as_markup()

@dp.message(Command("topmesaj"))
async def topmesaj_cmd(message: types.Message):
    if message.chat.type == "private": return
    await message.answer(f"📊 Reytinq Cədvəli 🇦🇿\n👤 İstifadəçi: {message.from_user.first_name}\n\nSıralama növü seçin:", reply_markup=get_reytinq_menyusu())

@dp.callback_query(F.data.startswith("top_"))
async def reytinq_goster(callback: types.CallbackQuery):
    kateqoriya = callback.data.split("_")[1]
    db_cursor.execute(f"SELECT scores.user_id, user_info.first_name, scores.msg_sayi FROM scores JOIN user_info ON scores.user_id = user_info.user_id WHERE scores.chat_id = ? AND scores.kateqoriya = ? ORDER BY scores.msg_sayi DESC LIMIT 10", (callback.message.chat.id, kateqoriya))
    rows = db_cursor.fetchall()
    res = f"📊 {kateqoriya.capitalize()} Reytinq:\n\n"
    if not rows: res += "Heç bir məlumat yoxdur."
    else:
        for i, row in enumerate(rows, 1): res += f"{i}. {row[1]} — {row[2]} mesaj\n"
    await callback.message.edit_text(res, reply_markup=get_reytinq_menyusu())

# ==========================================================
# 🚫 STİKER BLOKU
# ==========================================================

@dp.message(Command("stiker"))
async def stiker_cmd(message: types.Message, command: CommandObject):
    if message.chat.type == "private" or not await is_admin(message.chat.id, message.from_user.id): return
    if command.args == "on":
        db_cursor.execute("INSERT OR REPLACE INTO settings VALUES (?, 1)", (message.chat.id,))
        await message.answer("🚫 Stiker və Gif bloku aktiv edildi.")
    elif command.args == "off":
        db_cursor.execute("INSERT OR REPLACE INTO settings VALUES (?, 0)", (message.chat.id,))
        await message.answer("Stiker və Gif bloku deaktiv edildi.")
    db_conn.commit()

@dp.message()
async def global_handler(message: types.Message):
    if not message.chat or message.chat.type == "private": return
    u_id, c_id = message.from_user.id, message.chat.id
    db_cursor.execute("INSERT OR REPLACE INTO user_info VALUES (?, ?)", (u_id, message.from_user.first_name))
    
    if not (message.text and message.text.startswith("/")):
        nov = 'stiker' if message.sticker else ('gif' if message.animation else 'msg')
        for k in ["günlük", "həftəlik", "aylıq", "ümumi"]:
            db_cursor.execute(f"INSERT OR IGNORE INTO scores (chat_id, user_id, kateqoriya) VALUES (?, ?, ?)", (c_id, u_id, k))
            db_cursor.execute(f"UPDATE scores SET {nov}_sayi = {nov}_sayi + 1 WHERE chat_id = ? AND user_id = ? AND kateqoriya = ?", (c_id, u_id, k))
        db_conn.commit()

    db_cursor.execute("SELECT stiker_bloku FROM settings WHERE chat_id = ?", (c_id,))
    res = db_cursor.fetchone()
    if res and res[0] == 1 and (message.sticker or message.animation):
        try: await message.delete()
        except: pass

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
