import asyncio
import os
import sqlite3
import logging
import time
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# ==========================================================
# BOTUN ƏSAS KONFİQURASİYASI
# ==========================================================

OWNER_ID = 8024893255
API_TOKEN = "7886882115:AAEodWPGRhT6CQ-1rQgHy4ZKL_3wkKENe8Q"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ==========================================================
# MƏLUMAT BAZASI SİSTEMİ
# ==========================================================

def init_db():
    connection = sqlite3.connect("flower_security_ultra.db")
    cursor = connection.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS scores (chat_id INTEGER, user_id INTEGER, category TEXT, msg_count INTEGER DEFAULT 0, sticker_count INTEGER DEFAULT 0, gif_count INTEGER DEFAULT 0, PRIMARY KEY (chat_id, user_id, category))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_info (user_id INTEGER PRIMARY KEY, first_name TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings (chat_id INTEGER PRIMARY KEY, sticker_block INTEGER DEFAULT 0)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS warns (chat_id INTEGER, user_id INTEGER, count INTEGER DEFAULT 0, PRIMARY KEY (chat_id, user_id))''')
    connection.commit()
    return connection, cursor

db_conn, db_cursor = init_db()

# ==========================================================
# KÖMƏKÇİ FUNKSİYALAR
# ==========================================================

async def is_admin(chat_id: int, user_id: int):
    if user_id == OWNER_ID: return True
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ("administrator", "creator")
    except: return False

def parse_time(time_str: str):
    try:
        amount = int(time_str[:-1])
        unit = time_str[-1].lower()
        if unit == "m": return timedelta(minutes=amount)
        if unit == "h": return timedelta(hours=amount)
        if unit == "d": return timedelta(days=amount)
        return None
    except: return None

# ==========================================================
# 🏠 ÖZƏL ÇAT (DM) VƏ ÜMUMİ KOMANDALAR
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
    await message.answer(welcome_text)

@dp.message(Command("help"))
async def help_handler(message: types.Message):
    help_text = (
        f"🛠️ Botun Komandaları:\n\n"
        f"📊 Reytinq:\n"
        f"/topmesaj - Qrup reytinq menyusu\n"
        f"/my - Sizin şəxsi statistikanız\n\n"
        f"👮 Admin Funksiyaları (Yalnız qrupda):\n"
        f"/ban - İstifadəçini qovur\n"
        f"/unban - Banı açır\n"
        f"/mute - Səssizə alır\n"
        f"/unmute - Səsi açır\n"
        f"/warn - Xəbərdarlıq verir\n"
        f"/purge - Mesajları təmizləyir\n\n"
        f"⚙️ Quraşdırma (Qrup qurucusu):\n"
        f"/stiker off - Stikerləri bloklayır\n"
        f"/stiker on - Stikerləri açır"
    )
    await message.answer(help_text)

# ==========================================================
# 👤 ŞƏXSİ STATİSTİKA (/my)
# ==========================================================

@dp.message(Command("my"))
async def my_stats_handler(message: types.Message):
    u_id = message.from_user.id
    c_id = message.chat.id
    
    # Ümumi (total) statistikaya baxırıq
    db_cursor.execute(
        "SELECT msg_count, sticker_count, gif_count FROM scores WHERE user_id = ? AND category = 'total'", 
        (u_id,)
    )
    row = db_cursor.fetchone()
    
    if row:
        stats_text = (
            f"👤 {message.from_user.first_name}, sənin statistikan:\n\n"
            f"✉️ Mesaj sayı: {row[0]}\n"
            f"🖼️ Stiker sayı: {row[1]}\n"
            f"🎥 Gif sayı: {row[2]}\n\n"
            f"🌟 Aktivliyini artırmağa davam et!"
        )
    else:
        stats_text = "❌ Hələ ki, sənin haqqında bir məlumat tapılmadı. Bir az mesaj yaz, sonra yenidən yoxla!"
    
    await message.answer(stats_text)

# ==========================================================
# 👮 ADMİN KOMANDALARI
# ==========================================================

@dp.message(Command("ban"))
async def ban_handler(message: types.Message):
    if message.chat.type == "private": return
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message:
        return await message.answer("⚠️ Ban etmək üçün istifadəçini cavablayın.")
    try:
        await bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
        await message.answer(f"🚫 {message.reply_to_message.from_user.first_name} qovuldu.")
    except Exception as e: await message.answer(f"❌ Xəta: {e}")

@dp.message(Command("unban"))
async def unban_handler(message: types.Message):
    if message.chat.type == "private": return
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    await bot.unban_chat_member(message.chat.id, message.reply_to_message.from_user.id, only_if_banned=True)
    await message.answer(f"✅ {message.reply_to_message.from_user.first_name} banı açıldı.")

# ==========================================================
# 📊 REYTİNQ (/topmesaj)
# ==========================================================

def get_score_menu():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📅 Günlük", callback_data="score_daily"), InlineKeyboardButton(text="📅 Həftəlik", callback_data="score_weekly"), InlineKeyboardButton(text="📅 Aylıq", callback_data="score_monthly"))
    builder.row(InlineKeyboardButton(text="📊 Ümumi Reytinq", callback_data="score_total"))
    builder.row(InlineKeyboardButton(text="📄 Məlumat", callback_data="score_detail"), InlineKeyboardButton(text="🌐 Qlobal", callback_data="score_global"))
    return builder.as_markup()

@dp.message(Command("topmesaj"))
async def topmesaj_cmd(message: types.Message):
    if message.chat.type == "private": return await message.answer("ℹ️ Reytinq yalnız qruplarda işləyir.")
    await message.answer(f"📊 Message Scor Azerbaycan 🇦🇿\n👤 İstifadəçi: {message.from_user.first_name}\n\n👥 Sıralama növü seçin:", reply_markup=get_score_menu())

@dp.callback_query(F.data.startswith("score_"))
async def process_score(callback: types.CallbackQuery):
    cat = callback.data.split("_")[1]
    if cat in ["detail", "global"]: return await callback.answer("ℹ️ Tezliklə!", show_alert=True)
    db_cursor.execute(f"SELECT scores.user_id, user_info.first_name, scores.msg_count FROM scores JOIN user_info ON scores.user_id = user_info.user_id WHERE scores.chat_id = ? AND scores.category = ? ORDER BY scores.msg_count DESC LIMIT 10", (callback.message.chat.id, cat))
    rows = db_cursor.fetchall()
    res = f"📊 Sıralama: {cat}\n\n"
    for i, row in enumerate(rows, 1): res += f"{i}. {row[1]} - {row[2]} mesaj\n"
    await callback.message.edit_text(res or "❌ Məlumat yoxdur.", reply_markup=get_score_menu())

# ==========================================================
# ⚙️ AYARLAR VƏ QLOBAL SAYĞAC
# ==========================================================

@dp.message(Command("stiker"))
async def stiker_cmd(message: types.Message, command: CommandObject):
    if message.chat.type == "private" or not await is_admin(message.chat.id, message.from_user.id): return
    val = 1 if command.args == "off" else 0
    db_cursor.execute("INSERT OR REPLACE INTO settings VALUES (?, ?)", (message.chat.id, val))
    db_conn.commit()
    await message.answer("🚫 Stiker və Gif bloku aktiv edildi." if val else "🔓 Stiker və Gif bloku deaktiv edildi.")

@dp.message()
async def global_handler(message: types.Message):
    if not message.chat or message.chat.type == "private": 
        # Özəldə komanda deyilsə, sayğac işləmir
        return
    
    u_id, c_id = message.from_user.id, message.chat.id
    db_cursor.execute("INSERT OR REPLACE INTO user_info VALUES (?, ?)", (u_id, message.from_user.first_name))
    
    if not (message.text and message.text.startswith("/")):
        m_type = 'sticker' if message.sticker else ('gif' if message.animation else 'msg')
        for cat in ["daily", "weekly", "monthly", "total"]:
            db_cursor.execute(f"INSERT OR IGNORE INTO scores (chat_id, user_id, category) VALUES (?, ?, ?)", (c_id, u_id, cat))
            db_cursor.execute(f"UPDATE scores SET {m_type}_count = {m_type}_count + 1 WHERE chat_id = ? AND user_id = ? AND category = ?", (c_id, u_id, cat))
        db_conn.commit()

    db_cursor.execute("SELECT sticker_block FROM settings WHERE chat_id = ?", (c_id,))
    res = db_cursor.fetchone()
    if res and res[0] == 1 and (message.sticker or message.animation):
        try: await message.delete()
        except: pass

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
