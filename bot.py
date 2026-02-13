import asyncio
import os
import sqlite3
import logging
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder

# =====================
# KONFİQURASİYA
# =====================
OWNER_ID = 8024893255
# @BotFather-dən aldığın tokeni bura yaz:
API_TOKEN = "7886882115:AAEodWPGRhT6CQ-1rQgHy4ZKL_3wkKENe8Q"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# =====================
# SQLITE MƏLUMAT BAZASI (TAM GENİŞ)
# =====================
db_conn = sqlite3.connect("flower_security.db")
db_cursor = db_conn.cursor()

# Reytinq məlumatları
db_cursor.execute('''CREATE TABLE IF NOT EXISTS scores 
                 (chat_id INTEGER, user_id INTEGER, category TEXT, 
                 msg_count INTEGER DEFAULT 0, sticker_count INTEGER DEFAULT 0, gif_count INTEGER DEFAULT 0,
                 PRIMARY KEY (chat_id, user_id, category))''')

# İstifadəçi adları (Sıralama üçün)
db_cursor.execute('''CREATE TABLE IF NOT EXISTS user_info 
                 (user_id INTEGER PRIMARY KEY, first_name TEXT)''')

# Qrup ayarları (Stiker bloku və s.)
db_cursor.execute('''CREATE TABLE IF NOT EXISTS settings 
                 (chat_id INTEGER PRIMARY KEY, sticker_block INTEGER DEFAULT 0)''')

# Xəbərdarlıq sistemi
db_cursor.execute('''CREATE TABLE IF NOT EXISTS warns 
                 (chat_id INTEGER, user_id INTEGER, count INTEGER DEFAULT 0, 
                 PRIMARY KEY (chat_id, user_id))''')

db_conn.commit()

# =====================
# KÖMƏKÇİ FUNKSİYALAR
# =====================
async def is_admin(chat_id, user_id):
    if user_id == OWNER_ID: return True
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ("administrator", "creator")
    except: return False

async def is_creator_or_owner(chat_id, user_id):
    if user_id == OWNER_ID: return True
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status == "creator"
    except: return False

def parse_time(t):
    try:
        n = int(t[:-1])
        if t.endswith("m"): return timedelta(minutes=n)
        if t.endswith("h"): return timedelta(hours=n)
        if t.endswith("d"): return timedelta(days=n)
    except: return None

# =====================
# MODERASİYA KOMANDALARI (HƏR BİRİ AYRI)
# =====================

@dp.message(Command("admin"))
async def admin_promote_handler(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    await bot.promote_chat_member(message.chat.id, message.reply_to_message.from_user.id, 
        can_manage_chat=True, can_delete_messages=True, can_restrict_members=True)
    await message.answer(f"✅ {message.reply_to_message.from_user.first_name} admin edildi.")

@dp.message(Command("ban"))
async def ban_handler(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    await bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
    await message.answer(f"🚫 {message.reply_to_message.from_user.first_name} qrupdan banlandı.")

@dp.message(Command("mute"))
async def mute_handler(message: types.Message, command: CommandObject):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    delta = parse_time(command.args) if command.args else None
    until = datetime.now() + delta if delta else None
    await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, 
        permissions=types.ChatPermissions(can_send_messages=False), until_date=until)
    await message.answer(f"🔇 {message.reply_to_message.from_user.first_name} səssizə alındı.")

@dp.message(Command("unmute"))
async def unmute_handler(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, 
        permissions=types.ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True))
    await message.answer("🔊 Səs açıldı.")

@dp.message(Command("warn"))
async def warn_handler(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    uid, cid = message.reply_to_message.from_user.id, message.chat.id
    db_cursor.execute("INSERT OR IGNORE INTO warns VALUES (?, ?, 0)", (cid, uid))
    db_cursor.execute("UPDATE warns SET count = count + 1 WHERE chat_id = ? AND user_id = ?", (cid, uid))
    db_conn.commit()
    db_cursor.execute("SELECT count FROM warns WHERE chat_id = ? AND user_id = ?", (cid, uid))
    count = db_cursor.fetchone()[0]
    if count >= 3:
        await bot.ban_chat_member(cid, uid)
        db_cursor.execute("UPDATE warns SET count = 0 WHERE chat_id = ? AND user_id = ?", (cid, uid))
        db_conn.commit()
        await message.answer("🚫 Limit (3/3) doldu, istifadəçi qovuldu.")
    else:
        await message.answer(f"⚠️ Xəbərdarlıq verildi: {count}/3")

@dp.message(Command("purge"))
async def purge_handler(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    for m_id in range(message.reply_to_message.message_id, message.message_id + 1):
        try: await bot.delete_message(message.chat.id, m_id)
        except: pass

# =====================
# MESSAGE SCOR (SKRİNŞOTDAKI DÜYMƏLƏR)
# =====================
def get_main_score_kb():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📅 Günlük", callback_data="top_daily"),
                types.InlineKeyboardButton(text="📅 Həftəlik", callback_data="top_weekly"),
                types.InlineKeyboardButton(text="📅 Aylıq", callback_data="top_monthly"))
    builder.row(types.InlineKeyboardButton(text="📊 Bütün zamanlarda", callback_data="top_total"))
    builder.row(types.InlineKeyboardButton(text="📄 Detaylı bilgi", callback_data="top_detail"),
                types.InlineKeyboardButton(text="🌐 Global Gruplar", callback_data="top_global"))
    return builder.as_markup()

@dp.message(Command("topmesaj"))
async def topmesaj_cmd(message: types.Message):
    if message.chat.type == "private": return
    text = (f"**Message Scor** 🇦🇿\n👤 {message.from_user.first_name}\n"
            f"/topmesaj\n\n👥 **Bulunduğunuz grup** için sıralama türünü seçiniz.")
    await message.answer(text, reply_markup=get_main_score_kb(), parse_mode="Markdown")

@dp.callback_query(F.data == "back_to_main")
async def back_callback(callback: types.CallbackQuery):
    await callback.message.edit_text(f"**Message Scor** 🇦🇿\n👤 {callback.from_user.first_name}\n\nSıralama türünü seçiniz:", 
                                     reply_markup=get_main_score_kb(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("top_"))
async def score_process_callback(callback: types.CallbackQuery):
    cat = callback.data.split("_")[1]
    if cat in ["detail", "global"]:
        await callback.answer("ℹ️ Tezliklə aktiv olacaq!", show_alert=True)
        return

    db_cursor.execute(f"""
        SELECT scores.user_id, user_info.first_name, scores.msg_count 
        FROM scores JOIN user_info ON scores.user_id = user_info.user_id 
        WHERE scores.chat_id = ? AND scores.category = ? 
        ORDER BY scores.msg_count DESC LIMIT 10
    """, (callback.message.chat.id, cat))
    
    rows = db_cursor.fetchall()
    cat_title = {"daily": "Günlük", "weekly": "Haftalık", "monthly": "Aylık", "total": "Bütün Zamanlar"}[cat]
    
    res_text = f"📊 **{cat_title} Sıralama**\n\n"
    if not rows:
        res_text += "Məlumat tapılmadı."
    else:
        for i, row in enumerate(rows, 1):
            res_text += f"{i}. {row[1]} — `{row[2]}` mesaj\n"
    
    back_kb = InlineKeyboardBuilder()
    back_kb.add(types.InlineKeyboardButton(text="⬅️ Geri", callback_data="back_to_main"))
    await callback.message.edit_text(res_text, reply_markup=back_kb.as_markup(), parse_mode="Markdown")

# =====================
# STİKER BLOKU (DÜZƏLDİLMİŞ MƏNTİQ)
# =====================
@dp.message(Command("stiker"))
async def stiker_toggle_handler(message: types.Message, command: CommandObject):
    if not await is_creator_or_owner(message.chat.id, message.from_user.id): return
    
    val = 1 if command.args == "on" else 0
    db_cursor.execute("INSERT OR REPLACE INTO settings (chat_id, sticker_block) VALUES (?, ?)", (message.chat.id, val))
    db_conn.commit()
    
    status = "aktiv (silinəcək) 🛡️" if val == 1 else "deaktiv (buraxılacaq) 🔓"
    await message.answer(f"🛡️ Stiker bloku {status} edildi.")

# =====================
# QLOBAL HANDLER (SAYĞAC VƏ SİLMƏ)
# =====================
@dp.message()
async def main_handler(message: types.Message):
    if not message.chat or message.chat.type == "private": return
    if message.text and message.text.startswith("/"): return

    chat_id, user_id = message.chat.id, message.from_user.id
    db_cursor.execute("INSERT OR REPLACE INTO user_info VALUES (?, ?)", (user_id, message.from_user.first_name))
    
    # Sayğac növünü təyin et
    m_type = 'msg'
    if message.sticker: m_type = 'sticker'
    elif message.animation: m_type = 'gif'

    # Bütün kateqoriyalar üzrə artır
    for category in ["daily", "weekly", "monthly", "total"]:
        db_cursor.execute(f"INSERT OR IGNORE INTO scores (chat_id, user_id, category) VALUES (?, ?, ?)", (chat_id, user_id, category))
        db_cursor.execute(f"UPDATE scores SET {m_type}_count = {m_type}_count + 1 WHERE chat_id = ? AND user_id = ? AND category = ?", (chat_id, user_id, category))
    db_conn.commit()

    # Stiker blokunu yoxla
    db_cursor.execute("SELECT sticker_block FROM settings WHERE chat_id = ?", (chat_id,))
    res = db_cursor.fetchone()
    if res and res[0] == 1: # Əgər blok aktivdirsə
        if message.sticker or message.animation:
            try: await message.delete()
            except: pass

# =====================
# BOTU BAŞLAT
# =====================
async def main():
    print("Flower-Security Bot İşə Düşdü...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
  
