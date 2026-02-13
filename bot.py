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
# BOTUN ESAS KONFIQURASIYASI
# ==========================================================

# Senin ID-n (Botun sahibi)
OWNER_ID = 8024893255

# @BotFather-den aldigin API Tokeni bura daxil et:
API_TOKEN = "7886882115:AAEodWPGRhT6CQ-1rQgHy4ZKL_3wkKENe8Q"

# Bot ve Dispatcher obyektlerinin basladilmasi
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Logging sistemi (Xetalarin izlenmesi ucun ixtisarsiz)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ==========================================================
# MELUMAT BAZASI SISTEMI (SQLITE3)
# ==========================================================

def init_db():
    connection = sqlite3.connect("flower_security_ultra.db")
    cursor = connection.cursor()

    # 1. Message Scor (Reytinq) ucun cedvel
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scores (
            chat_id INTEGER, 
            user_id INTEGER, 
            category TEXT, 
            msg_count INTEGER DEFAULT 0, 
            sticker_count INTEGER DEFAULT 0, 
            gif_count INTEGER DEFAULT 0,
            PRIMARY KEY (chat_id, user_id, category)
        )
    ''')

    # 2. Istifadeci melumatlari (Adlar reytinqde gorunsun deye)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_info (
            user_id INTEGER PRIMARY KEY, 
            first_name TEXT
        )
    ''')

    # 3. Qrup Tenzimlemeleri (Stiker bloku ve s.)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            chat_id INTEGER PRIMARY KEY, 
            sticker_block INTEGER DEFAULT 0
        )
    ''')

    # 4. Xeberdarliq Sistemi (Warn)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS warns (
            chat_id INTEGER, 
            user_id INTEGER, 
            count INTEGER DEFAULT 0, 
            PRIMARY KEY (chat_id, user_id)
        )
    ''')

    connection.commit()
    return connection, cursor

db_conn, db_cursor = init_db()

# ==========================================================
# TEHLUKESIZLIK VE ADMIN YOXLANISLARI
# ==========================================================

async def is_admin(chat_id: int, user_id: int):
    if user_id == OWNER_ID:
        return True
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ("administrator", "creator")
    except Exception as e:
        logger.error(f"Admin yoxlanisinda xeta: {e}")
        return False

async def is_creator_or_owner(chat_id: int, user_id: int):
    if user_id == OWNER_ID:
        return True
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status == "creator"
    except Exception:
        return False

def parse_time(time_str: str):
    try:
        amount = int(time_str[:-1])
        unit = time_str[-1].lower()
        if unit == "m":
            return timedelta(minutes=amount)
        elif unit == "h":
            return timedelta(hours=amount)
        elif unit == "d":
            return timedelta(days=amount)
        return None
    except Exception:
        return None

# ==========================================================
# ADMIN KOMANDALARI (TAM VE IXTISARSIZ)
# ==========================================================

@dp.message(Command("admin"))
async def promote_handler(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        await message.answer("⚠️ Xeber: Admin etmek ucun istifadecini cavablayin.")
        return
    
    try:
        await bot.promote_chat_member(
            chat_id=message.chat.id,
            user_id=message.reply_to_message.from_user.id,
            can_manage_chat=True,
            can_delete_messages=True,
            can_restrict_members=True,
            can_invite_users=True,
            can_pin_messages=True
        )
        await message.answer(f"✅ Qebul: {message.reply_to_message.from_user.first_name} admin teyin olundu.")
    except Exception as e:
        await message.answer(f"❌ Xeta: {e}")

@dp.message(Command("ban"))
async def ban_handler(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        return
    
    try:
        await bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
        await message.answer(f"🚫 Ban: {message.reply_to_message.from_user.first_name} qrupdan qovuldu.")
    except Exception as e:
        await message.answer(f"❌ Xeta: {e}")

@dp.message(Command("unban"))
async def unban_handler(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        return
    
    await bot.unban_chat_member(message.chat.id, message.reply_to_message.from_user.id, only_if_banned=True)
    await message.answer(f"✅ Qebul: {message.reply_to_message.from_user.first_name} bani acildi.")

@dp.message(Command("mute"))
async def mute_handler(message: types.Message, command: CommandObject):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        return
    
    duration = parse_time(command.args) if command.args else None
    until = datetime.now() + duration if duration else None
    
    try:
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=message.reply_to_message.from_user.id,
            permissions=types.ChatPermissions(can_send_messages=False),
            until_date=until
        )
        time_msg = f" {command.args} muddetine" if command.args else ""
        await message.answer(f"🔇 Sessiz: {message.reply_to_message.from_user.first_name}{time_msg} sessize alindi.")
    except Exception as e:
        await message.answer(f"❌ Xeta: {e}")

@dp.message(Command("unmute"))
async def unmute_handler(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        return
    
    await bot.restrict_chat_member(
        chat_id=message.chat.id,
        user_id=message.reply_to_message.from_user.id,
        permissions=types.ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True
        )
    )
    await message.answer(f"🔊 Ses: {message.reply_to_message.from_user.first_name} sesi acildi.")

@dp.message(Command("warn"))
async def warn_handler(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        return
    
    u_id = message.reply_to_message.from_user.id
    c_id = message.chat.id
    
    db_cursor.execute("INSERT OR IGNORE INTO warns VALUES (?, ?, 0)", (c_id, u_id))
    db_cursor.execute("UPDATE warns SET count = count + 1 WHERE chat_id = ? AND user_id = ?", (c_id, u_id))
    db_conn.commit()
    
    db_cursor.execute("SELECT count FROM warns WHERE chat_id = ? AND user_id = ?", (c_id, u_id))
    cnt = db_cursor.fetchone()[0]
    
    if cnt >= 3:
        await bot.ban_chat_member(c_id, u_id)
        db_cursor.execute("UPDATE warns SET count = 0 WHERE chat_id = ? AND user_id = ?", (c_id, u_id))
        db_conn.commit()
        await message.answer(f"🚫 Ban: {message.reply_to_message.from_user.first_name} 3 xeberdarliq sebebi ile banlandi.")
    else:
        await message.answer(f"⚠️ Xeberdarliq: {message.reply_to_message.from_user.first_name} xeberdarliq aldi: {cnt}/3")

@dp.message(Command("purge"))
async def purge_handler(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        return
    
    start = message.reply_to_message.message_id
    end = message.message_id
    
    for m_id in range(start, end + 1):
        try:
            await bot.delete_message(message.chat.id, m_id)
        except Exception:
            continue
    
    notif = await message.answer("🧹 Temizlendi: Mesajlar silindi.")
    await asyncio.sleep(3)
    try:
        await notif.delete()
    except:
        pass

# ==========================================================
# MESSAGE SCOR (REYTINQ VE BACK DUYMESI)
# ==========================================================

def get_score_menu():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📅 Günlük", callback_data="score_daily"),
        InlineKeyboardButton(text="📅 Həftəlik", callback_data="score_weekly"),
        InlineKeyboardButton(text="📅 Aylıq", callback_data="score_monthly")
    )
    builder.row(
        InlineKeyboardButton(text="📊 Bütün zamanlarda", callback_data="score_total")
    )
    builder.row(
        InlineKeyboardButton(text="📄 Ətraflı Məlumat", callback_data="score_detail"),
        InlineKeyboardButton(text="🌐 Qlobal qruplar", callback_data="score_global")
    )
    return builder.as_markup()

@dp.message(Command("topmesaj"))
async def topmesaj_cmd(message: types.Message):
    if message.chat.type == "private":
        return
    
    text = (
        f"📊 Message Scor 🇦🇿\n"
        f"👤 İstifatəçi: {message.from_user.first_name}\n\n"
        f"👥 Bu qrup üçün sırlama növünü seçin."
    )
    await message.answer(text, reply_markup=get_score_menu())

@dp.callback_query(F.data == "back_to_main")
async def back_to_main_callback(callback: types.CallbackQuery):
    text = (
        f"📊 Message Scor\n"
        f"👤 İstifadəçi: {callback.from_user.first_name}\n\n"
        f"👥 Bu qrup üçün sıralama növünü seçin."
    )
    await callback.message.edit_text(text, reply_markup=get_score_menu())

@dp.callback_query(F.data.startswith("score_"))
async def process_score_callbacks(callback: types.CallbackQuery):
    cat = callback.data.split("_")[1]
    
    if cat in ["detail", "global"]:
        await callback.answer("ℹ️ Məlumat: Bu funksiya tezlikle aktiv olacaq!", show_alert=True)
        return

    db_cursor.execute(f"""
        SELECT scores.user_id, user_info.first_name, scores.msg_count 
        FROM scores 
        JOIN user_info ON scores.user_id = user_info.user_id 
        WHERE scores.chat_id = ? AND scores.category = ? 
        ORDER BY scores.msg_count DESC LIMIT 10
    """, (callback.message.chat.id, cat))
    
    rows = db_cursor.fetchall()
    titles = {"daily": "Gunluk", "weekly": "Heftelik", "monthly": "Ayliq", "total": "Umumi"}
    
    result_text = f"📊 Siralama: {titles[cat]} (Top 10)\n\n"
    if not rows:
        result_text += "❌ Heç bir data tapılmadı."
    else:
        for i, row in enumerate(rows, 1):
            result_text += f"{i}. {row[1]} - {row[2]} mesaj\n"
    
    back_kb = InlineKeyboardBuilder()
    back_kb.add(InlineKeyboardButton(text="⬅️ Geri Qayıt", callback_data="back_to_main"))
    
    await callback.message.edit_text(result_text, reply_markup=back_kb.as_markup())

# ==========================================================
# STIKER VE MEDIA KONTROLU (TERS MENTIQ)
# ==========================================================

@dp.message(Command("stiker"))
async def stiker_control_cmd(message: types.Message, command: CommandObject):
    if not await is_creator_or_owner(message.chat.id, message.from_user.id):
        return
    
    if command.args == "off":
        db_cursor.execute("INSERT OR REPLACE INTO settings (chat_id, sticker_block) VALUES (?, 1)", (message.chat.id,))
        db_conn.commit()
        await message.answer("🚫 Stiker və Gif bloku aktiv edildi.")
    elif command.args == "on":
        db_cursor.execute("INSERT OR REPLACE INTO settings (chat_id, sticker_block) VALUES (?, 0)", (message.chat.id,))
        db_conn.commit()
        await message.answer("Stiker və gif bloku deaktiv edildi.")
    else:
        await message.answer("ℹ️ İstifadə: /stiker off ve ya /stiker on")

# ==========================================================
# QLOBAL MESAJ SAYGACI VE BLOKLAMA SISTEMI
# ==========================================================

@dp.message()
async def global_handler(message: types.Message):
    if not message.chat or message.chat.type == "private":
        return
    
    u_id = message.from_user.id
    c_id = message.chat.id
    
    db_cursor.execute("INSERT OR REPLACE INTO user_info (user_id, first_name) VALUES (?, ?)", (u_id, message.from_user.first_name))
    
    if message.text and message.text.startswith("/"):
        return

    m_type = 'msg'
    if message.sticker:
        m_type = 'sticker'
    elif message.animation:
        m_type = 'gif'
    
    for cat in ["daily", "weekly", "monthly", "total"]:
        db_cursor.execute(f"INSERT OR IGNORE INTO scores (chat_id, user_id, category) VALUES (?, ?, ?)", (c_id, u_id, cat))
        db_cursor.execute(f"UPDATE scores SET {m_type}_count = {m_type}_count + 1 WHERE chat_id = ? AND user_id = ? AND category = ?", (c_id, u_id, cat))
    
    db_conn.commit()

    db_cursor.execute("SELECT sticker_block FROM settings WHERE chat_id = ?", (c_id,))
    st_res = db_cursor.fetchone()
    
    if st_res and st_res[0] == 1:
        if message.sticker or message.animation:
            try:
                await message.delete()
            except Exception:
                pass

# ==========================================================
# BOTUN BASLADILMASI
# ==========================================================

async def main():
    print("🚀 Flower-Security Bot Hazirdir")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("🛑 Bot sonduruldu.")
