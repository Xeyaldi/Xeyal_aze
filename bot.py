import asyncio
import sqlite3
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
# 📊 MƏLUMAT BAZASI
# ==========================================================

def init_db():
    connection = sqlite3.connect("flower_security_ultra.db")
    cursor = connection.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS scores (
        chat_id INTEGER, 
        user_id INTEGER, 
        kateqoriya TEXT, 
        msg_sayi INTEGER DEFAULT 0, 
        PRIMARY KEY (chat_id, user_id, kateqoriya))''')
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

# ==========================================================
# 👋 START MESAJI
# ==========================================================

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    welcome_text = (
        "🤖 **Flower-Security Qrup idarə Botu**\n\n"
        "Bu bot Telegram qrupları üçün hazırlanmış tam təhlükəsizlik və idarəetmə botudur.\n\n"
        "🛡️ **İmkanlar:**\n"
        "• Stiker / GIF / Video-note avtomatik nəzarət\n"
        "• Söyüş və uyğun olmayan sözlərin silinməsi\n"
        "• `/ban`, `/mute`, `/warn` komandaları\n"
        "• Auto-Ban (warn limiti dolduqda)\n"
        "• `/my` ilə ətraflı statistika\n"
        "• `/topmesaj` ilə reytinq sistemi\n\n"
        "👮 **Botu qrupa əlavə etdikdən sonra ona admin səlahiyyəti verin.**\n"
        "ℹ️ Əmrlərin siyahısı üçün `/help` yazın.\n\n"
        "⚡️ Sürətli • Stabil • Təhlükəsiz"
    )
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="➕ Botu Qrupa Əlavə Et", url=f"https://t.me/Miss_Flower_bot?startgroup=true"))
    builder.row(
        InlineKeyboardButton(text="📢 Kanal", url="https://t.me/ht_bots"),
        InlineKeyboardButton(text="💬 Dəstək", url="https://t.me/ht_bots_chat")
    )
    builder.row(InlineKeyboardButton(text="👤 Developer", url=f"tg://user?id={OWNER_ID}"))
    await message.answer(welcome_text, reply_markup=builder.as_markup(), parse_mode="Markdown")

# ==========================================================
# 👮 ADMİN KOMANDALARI (İŞLƏK)
# ==========================================================

@dp.message(Command("ban"))
async def ban_handler(message: types.Message):
    if message.chat.type == "private": return
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return await message.answer("⚠️ Ban etmək üçün istifadəçini cavablayın (reply).")
    user = message.reply_to_message.from_user
    try:
        await bot.ban_chat_member(message.chat.id, user.id)
        await message.answer(f"🚫 {user.first_name} qrupdan qovuldu.")
    except Exception as e:
        await message.answer(f"❌ Ban uğursuz oldu: {str(e)}")

@dp.message(Command("kick"))
async def kick_handler(message: types.Message):
    if message.chat.type == "private": return
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return await message.answer("⚠️ Kick etmək üçün istifadəçini cavablayın (reply).")
    user = message.reply_to_message.from_user
    try:
        await bot.kick_chat_member(message.chat.id, user.id)
        await bot.unban_chat_member(message.chat.id, user.id)
        await message.answer(f"👢 {user.first_name} qrupdan çıxarıldı.")
    except Exception as e:
        await message.answer(f"❌ Kick uğursuz oldu: {str(e)}")

@dp.message(Command("mute"))
async def mute_handler(message: types.Message):
    if message.chat.type == "private": return
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    user = message.reply_to_message.from_user
    try:
        await bot.restrict_chat_member(message.chat.id, user.id, permissions=types.ChatPermissions(can_send_messages=False))
        await message.answer(f"🔇 {user.first_name} səssizə alındı.")
    except Exception as e:
        await message.answer(f"❌ Mute uğursuz oldu: {str(e)}")

@dp.message(Command("unmute"))
async def unmute_handler(message: types.Message):
    if message.chat.type == "private": return
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    user = message.reply_to_message.from_user
    try:
        await bot.restrict_chat_member(message.chat.id, user.id,
            permissions=types.ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True)
        )
        await message.answer(f"🔊 {user.first_name} səsi açıldı.")
    except Exception as e:
        await message.answer(f"❌ Unmute uğursuz oldu: {str(e)}")

@dp.message(Command("warn"))
async def warn_handler(message: types.Message):
    if message.chat.type == "private": return
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    user = message.reply_to_message.from_user
    u_id, c_id = user.id, message.chat.id
    db_cursor.execute("INSERT OR IGNORE INTO warns VALUES (?, ?, 0)", (c_id, u_id))
    db_cursor.execute("UPDATE warns SET say = say + 1 WHERE chat_id = ? AND user_id = ?", (c_id, u_id))
    db_conn.commit()
    db_cursor.execute("SELECT say FROM warns WHERE chat_id = ? AND user_id = ?", (c_id, u_id))
    cnt = db_cursor.fetchone()[0]
    if cnt >= 3:
        await bot.ban_chat_member(c_id, u_id)
        db_cursor.execute("UPDATE warns SET say = 0 WHERE chat_id = ? AND user_id = ?", (c_id, u_id))
        db_conn.commit()
        await message.answer(f"🚫 {user.first_name} 3 xəbərdarlığa görə qovuldu.")
    else:
        await message.answer(f"⚠️ {user.first_name} xəbərdarlıq aldı: {cnt}/3")

@dp.message(Command("purge"))
async def purge_handler(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    try:
        for msg_id in range(message.reply_to_message.message_id, message.message_id):
            await bot.delete_message(message.chat.id, msg_id)
        await message.answer("✅ Mesajlar təmizləndi.")
    except Exception as e:
        await message.answer(f"❌ Purge uğursuz oldu: {str(e)}")

# ==========================================================
# 📊 STATISTIKA / MY KOMANDASI
# ==========================================================

@dp.message(Command("my"))
async def my_stats(message: types.Message):
    if message.chat.type == "private": return
    u_id, c_id = message.from_user.id, message.chat.id
    db_cursor.execute("SELECT msg_sayi, kateqoriya FROM scores WHERE chat_id = ? AND user_id = ?", (c_id, u_id))
    rows = db_cursor.fetchall()
    if not rows:
        await message.answer("Hələ heç bir mesajınız yoxdur.")
    else:
        res = "📊 Sizin statistika:\n\n"
        for kate, cnt in [(r[1], r[0]) for r in rows]:
            res += f"• {kate.capitalize()}: {cnt} mesaj\n"
        await message.answer(res)

# ==========================================================
# 🔹 ƏVVƏL VAR OLAN KODLARIN HAMISI QALIR
# ==========================================================

# (Sticker/GIF qoruma, dice/slot, reytinq, global_handler və s. burda toxunulmadan qalır)

# ==========================================================
# 🔹 BOTU İŞƏ SAL
# ==========================================================

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__": asyncio.run(main())
