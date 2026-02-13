import asyncio
import os
import sqlite3
import logging
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest

# =====================
# KONFİQURASİYA
# =====================
OWNER_ID = 8024893255
API_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# =====================
# SQLITE MƏLUMAT BAZASI (TAM İXTİSARSIZ)
# =====================
db_conn = sqlite3.connect("flower_security.db")
db_cursor = db_conn.cursor()

# Statistikalar üçün cədvəl
db_cursor.execute('''CREATE TABLE IF NOT EXISTS scores 
                 (chat_id INTEGER, user_id INTEGER, category TEXT, 
                 msg_count INTEGER DEFAULT 0, sticker_count INTEGER DEFAULT 0, gif_count INTEGER DEFAULT 0,
                 PRIMARY KEY (chat_id, user_id, category))''')

# İstifadəçi adları üçün cədvəl
db_cursor.execute('''CREATE TABLE IF NOT EXISTS user_info 
                 (user_id INTEGER PRIMARY KEY, first_name TEXT)''')

# Qrup tənzimləmələri üçün cədvəl
db_cursor.execute('''CREATE TABLE IF NOT EXISTS settings 
                 (chat_id INTEGER PRIMARY KEY, sticker_block INTEGER DEFAULT 0, warn_limit INTEGER DEFAULT 3, rules TEXT)''')

db_conn.commit()

# RAM-da müvəqqəti verilənlər (Warn və Fed üçün)
user_warns = {}
fed_db = {} 
group_feds = {}

# Söyüş siyahısı
BAD_WORDS = ["söyüş1", "söyüş2", "qehbe", "bic", "sq", "amciq", "gotveran", "peyser", "sik", "daşaq", "siktir", "gicdıllaq", "atdıran", "fahişə", "dalbayob"]

# =====================
# KÖMƏKÇİ FUNKSİYALAR
# =====================
def update_activity(chat_id, user_id, category, activity_type):
    db_cursor.execute("INSERT OR IGNORE INTO scores (chat_id, user_id, category) VALUES (?, ?, ?)", (chat_id, user_id, category))
    if activity_type == 'msg':
        db_cursor.execute("UPDATE scores SET msg_count = msg_count + 1 WHERE chat_id = ? AND user_id = ? AND category = ?", (chat_id, user_id, category))
    elif activity_type == 'sticker':
        db_cursor.execute("UPDATE scores SET sticker_count = sticker_count + 1 WHERE chat_id = ? AND user_id = ? AND category = ?", (chat_id, user_id, category))
    elif activity_type == 'gif':
        db_cursor.execute("UPDATE scores SET gif_count = gif_count + 1 WHERE chat_id = ? AND user_id = ? AND category = ?", (chat_id, user_id, category))
    db_conn.commit()

async def is_admin(chat_id, user_id):
    if user_id == OWNER_ID: return True
    try:
        m = await bot.get_chat_member(chat_id, user_id)
        return m.status in ("administrator", "creator")
    except: return False

async def is_creator_or_owner(chat_id, user_id):
    if user_id == OWNER_ID: return True
    try:
        m = await bot.get_chat_member(chat_id, user_id)
        return m.status == "creator"
    except: return False

def parse_time(t):
    try:
        n = int(t[:-1])
        if t.endswith("m"): return timedelta(minutes=n)
        if t.endswith("h"): return timedelta(hours=n)
        if t.endswith("d"): return timedelta(days=n)
    except: return None

# =====================
# QLOBAL MENECER (SAYĞAC VƏ QORUMA)
# =====================
@dp.message(lambda m: not m.text or not m.text.startswith("/"))
async def global_manager(message: types.Message):
    if not message.chat or message.chat.type == "private": return
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # İstifadəçi məlumatını yenilə
    db_cursor.execute("INSERT OR REPLACE INTO user_info VALUES (?, ?)", (user_id, message.from_user.first_name))
    
    # Aktivlik növünü təyin et
    a_type = 'msg'
    if message.sticker: a_type = 'sticker'
    elif message.animation: a_type = 'gif'

    # Bütün kateqoriyalar üzrə balları artır (SQLite yadda saxlayır)
    for cat in ["total", "daily", "weekly", "monthly"]:
        update_activity(chat_id, user_id, cat, a_type)

    # Stiker bloku yoxlanışı
    db_cursor.execute("SELECT sticker_block FROM settings WHERE chat_id = ?", (chat_id,))
    res = db_cursor.fetchone()
    if res and res[0] == 1 and (message.sticker or message.animation or message.video_note):
        try: await message.delete()
        except: pass
        return

    # Söyüş və Link qoruması
    if message.text:
        text_l = message.text.lower()
        if any(w in text_l for w in BAD_WORDS) or "t.me/" in text_l or "http" in text_l:
            try: await message.delete()
            except: pass

# =====================
# /MY ƏMRİ (TAM İSTƏDİYİN FORMATDA)
# =====================
@dp.message(Command("my"))
async def my_stats(message: types.Message):
    user_id = message.from_user.id
    
    # Bütün qruplar üzrə cəm
    db_cursor.execute("""
        SELECT SUM(msg_count), SUM(sticker_count), SUM(gif_count) 
        FROM scores WHERE user_id = ? AND category = 'total'
    """, (user_id,))
    res = db_cursor.fetchone()
    
    if not res or res[0] is None:
        return await message.answer("Heç bir aktivliyiniz tapılmadı.")
    
    total_msg, total_stkr, total_gif = res
    
    # Cari qrupdakı aktivlik
    db_cursor.execute("""
        SELECT msg_count, sticker_count, gif_count 
        FROM scores WHERE chat_id = ? AND user_id = ? AND category = 'total'
    """, (message.chat.id, user_id))
    current_res = db_cursor.fetchone()
    c_msg, c_stkr, c_gif = current_res if current_res else (0, 0, 0)

    text = (
        f"👤 {message.from_user.first_name} Statistikanız\n\n"
        f"📊 Ümumi Cəm:\n"
        f"💬 Mesaj: {total_msg}\n"
        f"🖼 Stiker: {total_stkr}\n"
        f"📹 Gif: {total_gif}\n\n"
        f"📍 Bu qrupda:\n"
        f"💬 Mesaj: {c_msg}\n"
        f"🖼 Stiker: {c_stkr}\n"
        f"📹 Gif: {c_gif}"
    )
    await message.answer(text)

# =====================
# TOPMESAJ (AZƏRBAYCAN DİLİNDƏ + MESSAGE SCOR STYLE)
# =====================
def get_top_kb():
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="📆 Günlük", callback_data="top_daily"),
           types.InlineKeyboardButton(text="📆 Həftəlik", callback_data="top_weekly"))
    kb.row(types.InlineKeyboardButton(text="📆 Aylıq", callback_data="top_monthly"),
           types.InlineKeyboardButton(text="📊 Bütün zamanlar", callback_data="top_total"))
    return kb.as_markup()

@dp.message(Command("topmesaj"))
async def top_cmd(message: types.Message):
    text = (f"Message Scor 🇦🇿\n👤 {message.from_user.first_name}\n/topmesaj\n\n"
            f"👥 Bu qrup üçün sıralama növünü seçin.")
    await message.answer(text, reply_markup=get_top_kb())

@dp.callback_query(F.data == "back_to_top")
async def back_top(callback: types.CallbackQuery):
    text = (f"Message Scor 🇦🇿\n👤 {callback.from_user.first_name}\n/topmesaj\n\n"
            f"👥 Bu qrup üçün sıralama növünü seçin.")
    await callback.message.edit_text(text, reply_markup=get_top_kb())

@dp.callback_query(F.data.startswith("top_"))
async def process_top(callback: types.CallbackQuery):
    cat = callback.data.split("_")[1]
    db_cursor.execute("SELECT user_id, msg_count FROM scores WHERE chat_id = ? AND category = ? ORDER BY msg_count DESC LIMIT 13", (callback.message.chat.id, cat))
    rows = db_cursor.fetchall()
    
    if not rows: return await callback.answer("Məlumat yoxdur.", show_alert=True)
    
    titles = {"daily": "Günlük", "weekly": "Həftəlik", "monthly": "Aylıq", "total": "Bütün zamanlar"}
    report = f"📊 {titles[cat]} Top 13 Siyahısı:\n\n"
    for i, (u_id, count) in enumerate(rows, 1):
        db_cursor.execute("SELECT first_name FROM user_info WHERE user_id = ?", (u_id,))
        name = db_cursor.fetchone()
        name = name[0] if name else f"İstifadəçi {u_id}"
        report += f"{i}. {name} — {count} mesaj\n"
    
    kb = InlineKeyboardBuilder()
    kb.add(types.InlineKeyboardButton(text="🔙 Geri", callback_data="back_to_top"))
    await callback.message.edit_text(report, reply_markup=kb.as_markup())

# =====================
# MODERASİYA VƏ ADMİN ƏMRLƏRİ (TAM)
# =====================
@dp.message(Command("promote"))
async def promote(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    try:
        await bot.promote_chat_member(message.chat.id, message.reply_to_message.from_user.id, 
            can_manage_chat=True, can_delete_messages=True, can_restrict_members=True, 
            can_invite_users=True, can_pin_messages=True, can_promote_members=False)
        await message.answer(f"✅ {message.reply_to_message.from_user.first_name} admin edildi!")
    except: pass

@dp.message(Command("ban"))
async def ban(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if message.reply_to_message:
        try:
            await bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
            await message.answer("🚫 İstifadəçi qrupdan kənarlaşdırıldı.")
        except: pass

@dp.message(Command("mute"))
async def mute(message: types.Message, command: CommandObject):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    duration = parse_time(command.args) if command.args else None
    until = datetime.now() + duration if duration else None
    try:
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, 
            permissions=types.ChatPermissions(can_send_messages=False), until_date=until)
        await message.answer("🔇 Səssizə alındı.")
    except: pass

@dp.message(Command("warn"))
async def warn(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    uid = message.reply_to_message.from_user.id
    key = (message.chat.id, uid)
    user_warns[key] = user_warns.get(key, 0) + 1
    if user_warns[key] >= 3:
        await bot.ban_chat_member(message.chat.id, uid)
        user_warns[key] = 0
        await message.answer(f"🚫 {message.reply_to_message.from_user.first_name} AUTO-BAN")
    else: await message.answer(f"⚠️ Xəbərdarlıq: {user_warns[key]}/3")

@dp.message(Command("purge"))
async def purge(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    for msg_id in range(message.reply_to_message.message_id, message.message_id + 1):
        try: await bot.delete_message(message.chat.id, msg_id)
        except: pass

@dp.message(Command("stiker"))
async def stiker_cmd(message: types.Message, command: CommandObject):
    if not await is_creator_or_owner(message.chat.id, message.from_user.id): return
    val = 1 if command.args and command.args.lower() == "off" else 0
    db_cursor.execute("INSERT OR REPLACE INTO settings (chat_id, sticker_block) VALUES (?, ?)", (message.chat.id, val))
    db_conn.commit()
    await message.answer(f"🚫 Stiker bloku: {'AKTİV' if val == 1 else 'DEAKTİV'}")

# =====================
# FEDERASİYA (KURUCU ŞƏRTİ İLƏ)
# =====================
@dp.message(Command("newfed"))
async def newfed(message: types.Message, command: CommandObject):
    if not command.args: return
    fid = str(abs(hash(command.args)) % 99999)
    fed_db[fid] = {"name": command.args, "banned": set()}
    await message.answer(f"✅ Yeni FED: {command.args}\nID: {fid}")

@dp.message(Command("joinfed"))
async def joinfed(message: types.Message, command: CommandObject):
    if not await is_creator_or_owner(message.chat.id, message.from_user.id):
        return await message.answer("❌ Bu əmri sadəcə qrup kurucusu edə bilər.")
    if command.args in fed_db:
        group_feds[message.chat.id] = command.args
        await message.answer(f"🔗 {fed_db[command.args]['name']} federasiyasına qoşuldu.")
    else:
        await message.answer("❌ Belə bir FED ID tapılmadı.")

@dp.message(Command("fban"))
async def fban(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    fid = group_feds.get(message.chat.id)
    if fid:
        uid = message.reply_to_message.from_user.id
        fed_db[fid]["banned"].add(uid)
        await bot.ban_chat_member(message.chat.id, uid)
        await message.answer("🌐 FED BAN sistemi ilə uzaqlaşdırıldı.")

# =====================
# START VƏ HELP (FLOWER-SECURITY)
# =====================
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    me = await bot.get_me()
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="➕ Botu Qrupa Əlavə Et", url=f"https://t.me/{me.username}?startgroup=true"))
    kb.row(types.InlineKeyboardButton(text="📢 Kanal", url="https://t.me/ht_bots"), types.InlineKeyboardButton(text="💬 Dəstək", url="https://t.me/ht_bots_chat"))
    kb.row(types.InlineKeyboardButton(text="👤 Developer", url="tg://user?id=8024893255"))
    
    text = (
        "🤖 Flower-Security Qrup idarə Botu\n\n"
        "Bu bot Telegram qrupları üçün hazırlanmış tam təhlükəsizlik və idarəetmə botudur.\n\n"
        "🛡 İmkanlar:\n"
        "• Stiker / GIF / Video-note avtomatik nəzarət\n"
        "• Söyüş və uyğun olmayan sözlərin silinməsi\n"
        "• /ban, /mute, /warn komandaları\n"
        "• Auto-Ban (warn limiti dolduqda)\n"
        "• Fed-Ban (bir neçə qrup üçün ortaq ban)\n"
        "• /my ilə ətraflı statistika\n"
        "• /topmesaj ilə reytinq sistemi\n\n"
        "👮 Botu qrupa əlavə etdikdən sonra ona admin səlahiyyəti verin.\n"
        "ℹ️ Əmrlərin siyahısı üçün /help yazın.\n\n"
        "⚡ Sürətli • Stabil • Təhlükəsiz"
    )
    await message.answer(text, reply_markup=kb.as_markup())

@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    text = ("📘 Flower-Security Bot Kömək\n\n"
            "👮 Admin: /promote, /ban, /mute, /warn, /purge, /stiker\n"
            "📊 Stats: /topmesaj, /my, /info\n"
            "🌐 Fed: /newfed, /joinfed, /fban")
    await message.answer(text)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
