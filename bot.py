import asyncio
import sqlite3
import random
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# ==========================================================
# ⚙️ KONFİQURASİYA
# ==========================================================
OWNER_ID = 8024893255
API_TOKEN = "7886882115:AAEodWPGRhT6CQ-1rQgHy4ZKL_3wkKENe8Q"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# ==========================================================
# 📊 MƏLUMAT BAZASI (TAM GENİŞLİKDƏ)
# ==========================================================
def init_db():
    connection = sqlite3.connect("flower_security_ultra.db")
    cursor = connection.cursor()
    # Reytinq üçün tam cədvəl
    cursor.execute('''CREATE TABLE IF NOT EXISTS scores (
        chat_id INTEGER, user_id INTEGER, kateqoriya TEXT, 
        msg_sayi INTEGER DEFAULT 0, PRIMARY KEY (chat_id, user_id, kateqoriya))''')
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
# 👋 START MESAJI (ŞƏKİLDƏKİ KİMİ)
# ==========================================================
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    welcome_text = (
        "🤖 **Flower-Security Qrup idarə Botu**\n\n"
        "Bu bot Telegram qrupları üçün hazırlanmış "
        "tam təhlükəsizlik və idarəetmə botudur.\n\n"
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
    builder.row(InlineKeyboardButton(text="📢 Kanal", url="https://t.me/ht_bots"), InlineKeyboardButton(text="💬 Dəstək", url="https://t.me/ht_bots_chat"))
    builder.row(InlineKeyboardButton(text="🧑‍💻 Developer", url=f"tg://user?id={OWNER_ID}"))
    await message.answer(welcome_text, reply_markup=builder.as_markup(), parse_mode="Markdown")

# ==========================================================
# 📖 HELP MESAJI (DEDİYİN KİMİ GENİŞ)
# ==========================================================
@dp.message(Command("help"))
async def help_handler(message: types.Message):
    help_text = (
        "❓ **Kömək Menyusu**\n\n"
        "👮 **Admin Əmrləri:**\n"
        "• `/ban` - İstifadəçini qovur\n"
        "• `/mute` - İstifadəçini səssizə alır\n"
        "• `/unmute` - Səsi açır\n"
        "• `/warn` - Xəbərdarlıq verir (3/3 ban)\n"
        "• `/unwarn` - Xəbərdarlıqları silir\n"
        "• `/purge` - Mesajları təmizləyir\n"
        "• `/stiker on|off` - Stiker blokunu idarə edir\n\n"
        "📊 **Statistika:**\n"
        "• `/topmesaj` - Reytinq cədvəli\n"
        "• `/my` - Sizin aktivliyiniz\n\n"
        "🎲 **Əyləncə:**\n"
        "• `/dice`, `/slot`, `/basket`"
    )
    await message.answer(help_text, parse_mode="Markdown")

# ==========================================================
# 👮 ADMİN KOMANDALARI (REPLY YOXLANIŞI İLƏ)
# ==========================================================
@dp.message(Command("ban"))
async def ban_handler(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message:
        return await message.answer("⚠️ Ban etmək üçün istifadəçini cavablayın (reply).")
    try:
        await bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
        await message.answer(f"🚫 {message.reply_to_message.from_user.first_name} qrupdan qovuldu.")
    except: await message.answer("❌ Xəta: Admin qovula bilməz.")

@dp.message(Command("mute"))
async def mute_handler(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message:
        return await message.answer("⚠️ Səssizə almaq üçün istifadəçini cavablayın (reply).")
    try:
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, permissions=types.ChatPermissions(can_send_messages=False))
        await message.answer(f"🔇 {message.reply_to_message.from_user.first_name} səssizə alındı.")
    except: pass

@dp.message(Command("unmute"))
async def unmute_handler(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message:
        return await message.answer("⚠️ Səsi açmaq üçün istifadəçini cavablayın (reply).")
    try:
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, permissions=types.ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True))
        await message.answer(f"🔊 {message.reply_to_message.from_user.first_name} səsi açıldı.")
    except: pass

@dp.message(Command("warn"))
async def warn_handler(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message:
        return await message.answer("⚠️ Xəbərdarlıq etmək üçün istifadəçini cavablayın (reply).")
    
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
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message:
        return await message.answer("⚠️ Xəbərdarlığı silmək üçün istifadəçini cavablayın (reply).")
    db_cursor.execute("UPDATE warns SET say = 0 WHERE chat_id = ? AND user_id = ?", (message.chat.id, message.reply_to_message.from_user.id))
    db_conn.commit()
    await message.answer(f"✅ {message.reply_to_message.from_user.first_name} xəbərdarlıqları təmizləndi.")

# ==========================================================
# 📊 REYTİNQ (İXTİSARSIZ HAMSINI ƏLAVƏ ETDİM)
# ==========================================================
def get_top_kb():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📅 Günlük", callback_data="top_günlük"), InlineKeyboardButton(text="📅 Həftəlik", callback_data="top_həftəlik"))
    builder.row(InlineKeyboardButton(text="📅 Aylıq", callback_data="top_aylıq"), InlineKeyboardButton(text="📊 Ümumi", callback_data="top_ümumi"))
    return builder.as_markup()

@dp.message(Command("topmesaj"))
async def top_cmd(message: types.Message):
    if message.chat.type == "private": return
    await message.answer(f"📊 Reytinq Menyusu\n👤 İstifadəçi: {message.from_user.first_name}", reply_markup=get_top_kb())

@dp.callback_query(F.data.startswith("top_"))
async def process_top(callback: types.CallbackQuery):
    kat = callback.data.split("_")[1]
    db_cursor.execute(f"SELECT user_info.first_name, scores.msg_sayi FROM scores JOIN user_info ON scores.user_id = user_info.user_id WHERE scores.chat_id = ? AND scores.kateqoriya = ? ORDER BY scores.msg_sayi DESC LIMIT 10", (callback.message.chat.id, kat))
    rows = db_cursor.fetchall()
    res = f"📊 {kat.capitalize()} Reytinq:\n\n"
    if not rows: res += "Məlumat yoxdur."
    else:
        for i, row in enumerate(rows, 1): res += f"{i}. {row[0]} — {row[1]} mesaj\n"
    await callback.message.edit_text(res, reply_markup=get_top_kb())

# ==========================================================
# 🎲 ƏYLƏNCƏ
# ==========================================================
@dp.message(Command("dice"))
async def dice_h(message: types.Message): await message.answer_dice(emoji="🎲")
@dp.message(Command("slot"))
async def slot_h(message: types.Message): await message.answer_dice(emoji="🎰")
@dp.message(Command("basket"))
async def basket_h(message: types.Message): await message.answer_dice(emoji="🏀")

# ==========================================================
# 🛡️ STİKER BLOKU VƏ SAYĞAC
# ==========================================================
@dp.message(Command("stiker"))
async def stiker_cmd(message: types.Message, command: CommandObject):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if command.args == "off":
        db_cursor.execute("INSERT OR REPLACE INTO settings VALUES (?, 1)", (message.chat.id,))
        await message.answer("🛡️ Stiker bloku aktiv edildi.")
    elif command.args == "on":
        db_cursor.execute("INSERT OR REPLACE INTO settings VALUES (?, 0)", (message.chat.id,))
        await message.answer("🔓 Stiker bloku deaktiv edildi.")
    db_conn.commit()

@dp.message()
async def global_handler(message: types.Message):
    if not message.chat or message.chat.type == "private": return
    u_id, c_id = message.from_user.id, message.chat.id
    db_cursor.execute("INSERT OR REPLACE INTO user_info VALUES (?, ?)", (u_id, message.from_user.first_name))
    if not (message.text and message.text.startswith("/")):
        for k in ["günlük", "həftəlik", "aylıq", "ümumi"]:
            db_cursor.execute(f"INSERT OR IGNORE INTO scores (chat_id, user_id, kateqoriya) VALUES (?, ?, ?)", (c_id, u_id, k))
            db_cursor.execute(f"UPDATE scores SET msg_sayi = msg_sayi + 1 WHERE chat_id = ? AND user_id = ? AND kateqoriya = ?", (c_id, u_id, k))
        db_conn.commit()
    db_cursor.execute("SELECT stiker_bloku FROM settings WHERE chat_id = ?", (c_id,))
    res = db_cursor.fetchone()
    if res and res[0] == 1 and (message.sticker or message.animation):
        try: await message.delete()
        except: pass

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__": asyncio.run(main())
