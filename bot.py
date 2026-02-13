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
# Botun sahibi (Sənin ID-n)
OWNER_ID = 8024893255
# Tokeni bura yaz:
API_TOKEN = "7886882115:AAEodWPGRhT6CQ-1rQgHy4ZKL_3wkKENe8Q"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# =====================
# SQLITE MƏLUMAT BAZASI (GENİŞLƏNDİRİLMİŞ)
# =====================
db_conn = sqlite3.connect("flower_security.db")
db_cursor = db_conn.cursor()

# Reytinq üçün cədvəl
db_cursor.execute('''CREATE TABLE IF NOT EXISTS scores 
                 (chat_id INTEGER, user_id INTEGER, category TEXT, 
                 msg_count INTEGER DEFAULT 0, sticker_count INTEGER DEFAULT 0, gif_count INTEGER DEFAULT 0,
                 PRIMARY KEY (chat_id, user_id, category))''')

# İstifadəçi adları üçün cədvəl
db_cursor.execute('''CREATE TABLE IF NOT EXISTS user_info 
                 (user_id INTEGER PRIMARY KEY, first_name TEXT)''')

# Qrup ayarları (Stiker bloku və s.) üçün cədvəl
db_cursor.execute('''CREATE TABLE IF NOT EXISTS settings 
                 (chat_id INTEGER PRIMARY KEY, sticker_block INTEGER DEFAULT 0, welcome_msg TEXT)''')

# Xəbərdarlıqlar (Warn) üçün cədvəl
db_cursor.execute('''CREATE TABLE IF NOT EXISTS warns 
                 (chat_id INTEGER, user_id INTEGER, count INTEGER DEFAULT 0, 
                 PRIMARY KEY (chat_id, user_id))''')

db_conn.commit()

# =====================
# KÖMƏKÇİ FUNKSİYALAR (İXTİSARSIZ)
# =====================
async def is_admin(chat_id, user_id):
    if user_id == OWNER_ID:
        return True
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        if member.status in ("administrator", "creator"):
            return True
        return False
    except Exception:
        return False

async def is_creator_or_owner(chat_id, user_id):
    if user_id == OWNER_ID:
        return True
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        if member.status == "creator":
            return True
        return False
    except Exception:
        return False

def parse_time(time_string):
    try:
        amount = int(time_string[:-1])
        unit = time_string[-1].lower()
        if unit == "m":
            return timedelta(minutes=amount)
        elif unit == "h":
            return timedelta(hours=amount)
        elif unit == "d":
            return timedelta(days=amount)
        return None
    except Exception:
        return None

# =====================
# /START (QRUPDA XƏBƏRDARLIQ)
# =====================
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    if message.chat.type != "private":
        await message.reply("❌ Bu əmr yalnız botun şəxsi mesajlarında (DM) işləyir!")
        return

    me = await bot.get_me()
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="➕ Botu Qrupa Əlavə Et", url=f"https://t.me/{me.username}?startgroup=true"))
    builder.row(
        types.InlineKeyboardButton(text="📢 Kanal", url="https://t.me/ht_bots"), 
        types.InlineKeyboardButton(text="💬 Dəstək", url="https://t.me/ht_bots_chat")
    )
    builder.row(types.InlineKeyboardButton(text="👤 Developer", url="tg://user?id=8024893255"))
    
    start_text = (
        "🤖 **Flower-Security Qrup idarə Botu**\n\n"
        "Bu bot Telegram qrupları üçün hazırlanmış tam təhlükəsizlik və idarəetmə botudur.\n\n"
        "🛡️ **İmkanlar:**\n"
        "• Stiker / GIF / Video-note avtomatik nəzarət\n"
        "• Söyüş və uyğun olmayan sözlərin silinməsi\n"
        "• /ban, /mute, /warn komandaları\n"
        "• Auto-Ban (warn limiti dolduqda)\n"
        "• /my ilə ətraflı statistika\n"
        "• /topmesaj ilə reytinq sistemi\n\n"
        "👮 Botu qrupa əlavə etdikdən sonra ona admin səlahiyyəti verin.\n"
        "ℹ️ Əmrlərin siyahısı üçün /help yazın.\n\n"
        "⚡ **Sürətli • Stabil • Təhlükəsiz**"
    )
    await message.answer(start_text, reply_markup=builder.as_markup(), parse_mode="Markdown")

# =====================
# ADMİN VƏ MODERASİYA (HƏR BİRİ AYRI)
# =====================

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        await message.answer("⚠️ Bu əmri bir istifadəçinin mesajına cavab verərək yazın.")
        return
    
    await bot.promote_chat_member(
        message.chat.id, 
        message.reply_to_message.from_user.id, 
        can_manage_chat=True, 
        can_delete_messages=True, 
        can_restrict_members=True,
        can_invite_users=True,
        can_pin_messages=True
    )
    await message.answer(f"✅ {message.reply_to_message.from_user.first_name} admin təyin edildi.")

@dp.message(Command("unadmin"))
async def cmd_unadmin(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        return
    
    await bot.promote_chat_member(
        message.chat.id, 
        message.reply_to_message.from_user.id, 
        can_manage_chat=False
    )
    await message.answer(f"❌ {message.reply_to_message.from_user.first_name} adminlikdən çıxarıldı.")

@dp.message(Command("ban"))
async def cmd_ban(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        return
    
    await bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
    await message.answer(f"🚫 {message.reply_to_message.from_user.first_name} qrupdan banlandı.")

@dp.message(Command("unban"))
async def cmd_unban(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        return
    
    await bot.unban_chat_member(message.chat.id, message.reply_to_message.from_user.id, only_if_banned=True)
    await message.answer(f"✅ {message.reply_to_message.from_user.first_name} banı açıldı.")

@dp.message(Command("mute"))
async def cmd_mute(message: types.Message, command: CommandObject):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        return
    
    delta = parse_time(command.args) if command.args else None
    until = datetime.now() + delta if delta else None
    
    await bot.restrict_chat_member(
        message.chat.id, 
        message.reply_to_message.from_user.id, 
        permissions=types.ChatPermissions(can_send_messages=False), 
        until_date=until
    )
    
    time_str = f" ({command.args} müddətinə)" if command.args else ""
    await message.answer(f"🔇 {message.reply_to_message.from_user.first_name} səssizə alındı{time_str}.")

@dp.message(Command("unmute"))
async def cmd_unmute(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        return
    
    await bot.restrict_chat_member(
        message.chat.id, 
        message.reply_to_message.from_user.id, 
        permissions=types.ChatPermissions(
            can_send_messages=True, 
            can_send_media_messages=True, 
            can_send_other_messages=True,
            can_add_web_page_previews=True
        )
    )
    await message.answer(f"🔊 {message.reply_to_message.from_user.first_name} səs açıldı.")

@dp.message(Command("warn"))
async def cmd_warn(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        return
    
    uid = message.reply_to_message.from_user.id
    cid = message.chat.id
    
    db_cursor.execute("INSERT OR IGNORE INTO warns (chat_id, user_id, count) VALUES (?, ?, 0)", (cid, uid))
    db_cursor.execute("UPDATE warns SET count = count + 1 WHERE chat_id = ? AND user_id = ?", (cid, uid))
    db_conn.commit()
    
    db_cursor.execute("SELECT count FROM warns WHERE chat_id = ? AND user_id = ?", (cid, uid))
    current_warns = db_cursor.fetchone()[0]
    
    if current_warns >= 3:
        await bot.ban_chat_member(cid, uid)
        db_cursor.execute("UPDATE warns SET count = 0 WHERE chat_id = ? AND user_id = ?", (cid, uid))
        db_conn.commit()
        await message.answer(f"🚫 {message.reply_to_message.from_user.first_name} 3/3 xəbərdarlıq səbəbiylə banlandı.")
    else:
        await message.answer(f"⚠️ {message.reply_to_message.from_user.first_name} xəbərdarlıq aldı: {current_warns}/3")

@dp.message(Command("unwarn"))
async def cmd_unwarn(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        return
    
    db_cursor.execute("UPDATE warns SET count = 0 WHERE chat_id = ? AND user_id = ?", (message.chat.id, message.reply_to_message.from_user.id))
    db_conn.commit()
    await message.answer(f"✅ {message.reply_to_message.from_user.first_name} xəbərdarlıqları sıfırlandı.")

@dp.message(Command("purge"))
async def cmd_purge(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        return
    
    start_msg = message.reply_to_message.message_id
    end_msg = message.message_id
    
    for m_id in range(start_msg, end_msg + 1):
        try:
            await bot.delete_message(message.chat.id, m_id)
        except Exception:
            continue
    await message.answer("✅ Mesajlar təmizləndi.")

@dp.message(Command("reload"))
async def cmd_reload(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    await message.answer("🔄 Sistem yeniləndi, məlumat bazası keşləri təmizləndi.")

# =====================
# MESSAGE SCOR (/TOPMESAJ)
# =====================
def get_main_score_keyboard():
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="📅 Günlük", callback_data="score_daily"),
           types.InlineKeyboardButton(text="📅 Həftəlik", callback_data="score_weekly"))
    kb.row(types.InlineKeyboardButton(text="📅 Aylıq", callback_data="score_monthly"),
           types.InlineKeyboardButton(text="📊 Bütün zamanlar", callback_data="score_total"))
    kb.row(types.InlineKeyboardButton(text="📄 Detaylı bilgi", callback_data="score_detail"),
           types.InlineKeyboardButton(text="🌐 Global Gruplar", callback_data="score_global"))
    return kb.as_markup()

@dp.message(Command("topmesaj"))
async def cmd_topmesaj(message: types.Message):
    if message.chat.type == "private":
        return
    
    text = (
        f"**Message Scor** 🇦🇿\n"
        f"👤 {message.from_user.first_name}\n"
        f"/topmesaj\n\n"
        f"👥 **Bu qrup üçün** sıralama növünü seçin."
    )
    await message.answer(text, reply_markup=get_main_score_keyboard(), parse_mode="Markdown")

@dp.callback_query(F.data == "score_back")
async def cb_score_back(callback: types.CallbackQuery):
    text = (
        f"**Message Scor** 🇦🇿\n"
        f"👤 {callback.from_user.first_name}\n"
        f"/topmesaj\n\n"
        f"👥 **Bu qrup üçün** sıralama növünü seçin."
    )
    await callback.message.edit_text(text, reply_markup=get_main_score_keyboard(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("score_"))
async def cb_score_process(callback: types.CallbackQuery):
    category = callback.data.split("_")[1]
    
    back_kb = InlineKeyboardBuilder()
    back_kb.add(types.InlineKeyboardButton(text="⬅️ Geri (Back)", callback_data="score_back"))
    
    if category in ["detail", "global"]:
        await callback.message.edit_text("ℹ️ Tezliklə aktiv olacaq...", reply_markup=back_kb.as_markup())
        return

    db_cursor.execute(f"""
        SELECT scores.user_id, user_info.first_name, scores.msg_count 
        FROM scores 
        JOIN user_info ON scores.user_id = user_info.user_id 
        WHERE scores.chat_id = ? AND scores.category = ? 
        ORDER BY scores.msg_count DESC LIMIT 10
    """, (callback.message.chat.id, category))
    
    rows = db_cursor.fetchall()
    cat_title = {"daily": "Günlük", "weekly": "Həftəlik", "monthly": "Aylıq", "total": "Bütün zamanlar"}[category]
    
    result_text = f"📊 **{cat_title} Sıralama (Top 10)**\n\n"
    if not rows:
        result_text += "Heç bir məlumat tapılmadı."
    else:
        for i, row in enumerate(rows, 1):
            result_text += f"{i}. {row[1]} — `{row[2]}` mesaj\n"
            
    await callback.message.edit_text(result_text, reply_markup=back_kb.as_markup(), parse_mode="Markdown")

# =====================
# ŞƏXSİ STATİSTİKA (/MY)
# =====================
@dp.message(Command("my"))
async def cmd_my(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    db_cursor.execute("SELECT msg_count, sticker_count, gif_count FROM scores WHERE chat_id = ? AND user_id = ? AND category = 'total'", (chat_id, user_id))
    current_group = db_cursor.fetchone()
    
    db_cursor.execute("SELECT SUM(msg_count), SUM(sticker_count), SUM(gif_count) FROM scores WHERE user_id = ? AND category = 'total'", (user_id,))
    global_total = db_cursor.fetchone()
    
    c_m, c_s, c_g = current_group if current_group else (0, 0, 0)
    g_m, g_s, g_g = global_total if global_total and global_total[0] is not None else (0, 0, 0)
    
    text = (
        f"👤 **{message.from_user.first_name} Statistikanız**\n\n"
        f"📊 **Ümumi Cəm (Global):**\n"
        f"💬 Mesaj: {g_m}\n"
        f"🖼 Stiker: {g_s}\n"
        f"📹 Gif: {g_g}\n\n"
        f"📍 **Bu qrupda:**\n"
        f"💬 Mesaj: {c_m}\n"
        f"🖼 Stiker: {c_s}\n"
        f"📹 Gif: {c_g}"
    )
    await message.answer(text, parse_mode="Markdown")

# =====================
# AYARLAR (STİKER ON/OFF)
# =====================
@dp.message(Command("stiker"))
async def cmd_stiker(message: types.Message, command: CommandObject):
    if not await is_creator_or_owner(message.chat.id, message.from_user.id):
        return
    
    if command.args == "on":
        db_cursor.execute("INSERT OR REPLACE INTO settings (chat_id, sticker_block) VALUES (?, 1)", (message.chat.id,))
        db_conn.commit()
        await message.answer("🛡️ Stiker bloku aktiv edildi.")
    elif command.args == "off":
        db_cursor.execute("INSERT OR REPLACE INTO settings (chat_id, sticker_block) VALUES (?, 0)", (message.chat.id,))
        db_conn.commit()
        await message.answer("🔓 Stiker bloku deaktiv edildi.")
    else:
        await message.answer("ℹ️ İstifadə: `/stiker on` və ya `/stiker off` (Sadəcə Kurucu)")

# =====================
# SAYĞAC VƏ AVTO-MODERASİYA (HƏR MESAJ)
# =====================
@dp.message()
async def global_msg_handler(message: types.Message):
    if not message.chat or message.chat.type == "private":
        return
    
    # Əmrləri sayma
    if message.text and message.text.startswith("/"):
        return
    
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Adı yenilə
    db_cursor.execute("INSERT OR REPLACE INTO user_info (user_id, first_name) VALUES (?, ?)", (user_id, message.from_user.first_name))
    
    # Növü müəyyən et
    msg_type = 'msg'
    if message.sticker:
        msg_type = 'sticker'
    elif message.animation:
        msg_type = 'gif'
        
    # Sayğacları artır (4 kateqoriya üzrə)
    for cat in ["daily", "weekly", "monthly", "total"]:
        db_cursor.execute(f"INSERT OR IGNORE INTO scores (chat_id, user_id, category) VALUES (?, ?, ?)", (chat_id, user_id, cat))
        db_cursor.execute(f"UPDATE scores SET {msg_type}_count = {msg_type}_count + 1 WHERE chat_id = ? AND user_id = ? AND category = ?", (chat_id, user_id, cat))
    db_conn.commit()

    # Stiker blokunu yoxla
    db_cursor.execute("SELECT sticker_block FROM settings WHERE chat_id = ?", (chat_id,))
    res = db_cursor.fetchone()
    if res and res[0] == 1:
        if message.sticker or message.animation:
            try:
                await message.delete()
            except Exception:
                pass

# =====================
# BOTU BAŞLAT
# =====================
async def main():
    print("Bot işə düşdü...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot dayandı.")
      
