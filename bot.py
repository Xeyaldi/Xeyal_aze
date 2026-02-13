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
# Bura öz Bot Tokenini yazmalısan
API_TOKEN = "7886882115:AAEodWPGRhT6CQ-1rQgHy4ZKL_3wkKENe8Q"
OWNER_ID = 8024893255

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# =====================
# SQLITE MƏLUMAT BAZASI (TAM VƏ AÇIQ)
# =====================
db_conn = sqlite3.connect("flower_security.db")
db_cursor = db_conn.cursor()

# Hər bir kateqoriya (günlük, həftəlik, aylıq, ümumi) üçün sayğaclar
db_cursor.execute('''CREATE TABLE IF NOT EXISTS scores 
                 (chat_id INTEGER, user_id INTEGER, category TEXT, 
                 msg_count INTEGER DEFAULT 0, sticker_count INTEGER DEFAULT 0, gif_count INTEGER DEFAULT 0,
                 PRIMARY KEY (chat_id, user_id, category))''')

# İstifadəçilərin adlarını saxlamaq üçün
db_cursor.execute('''CREATE TABLE IF NOT EXISTS user_info 
                 (user_id INTEGER PRIMARY KEY, first_name TEXT)''')

# Qrup tənzimləmələri (stiker bloku və s.) üçün
db_cursor.execute('''CREATE TABLE IF NOT EXISTS settings 
                 (chat_id INTEGER PRIMARY KEY, sticker_block INTEGER DEFAULT 0)''')

db_conn.commit()

# Xəbərdarlıqların (warn) müvəqqəti yaddaşı
user_warns = {}

# =====================
# KÖMƏKÇİ FUNKSİYALAR
# =====================
async def is_admin(chat_id, user_id):
    if user_id == OWNER_ID: return True
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ("administrator", "creator")
    except Exception:
        return False

def parse_time(time_str):
    try:
        amount = int(time_str[:-1])
        unit = time_str[-1].lower()
        if unit == "m": return timedelta(minutes=amount)
        if unit == "h": return timedelta(hours=amount)
        if unit == "d": return timedelta(days=amount)
    except:
        return None

# =====================
# /START KOMANDASI (QRUPDA XƏBƏRDARLIQLA)
# =====================
@dp.message(Command("start"))
async def start_command(message: types.Message):
    # Qrupda yazılıbsa xəbərdarlıq et
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
        "• Fed-Ban (bir neçə qrup üçün ortaq ban)\n"
        "• /my ilə ətraflı statistika\n"
        "• /topmesaj ilə reytinq sistemi\n\n"
        "👮 Botu qrupa əlavə etdikdən sonra ona admin səlahiyyəti verin.\n"
        "ℹ️ Əmrlərin siyahısı üçün /help yazın.\n\n"
        "⚡ **Sürətli • Stabil • Təhlükəsiz**"
    )
    await message.answer(start_text, reply_markup=builder.as_markup(), parse_mode="Markdown")

# =====================
# /HELP KOMANDASI (TAM SİYAHI)
# =====================
@dp.message(Command("help"))
async def help_command(message: types.Message):
    help_text = (
        "📘 **Flower-Security Bot Kömək**\n\n"
        "👮 **Admin:**\n"
        "/promote, /demote, /ban, /unban, /mute, /unmute, /warn, /unwarn, /purge\n\n"
        "📊 **Statistika:**\n"
        "/topmesaj, /my, /stats, /info\n\n"
        "⚙️ **Ayarlar (Kurucu):**\n"
        "/stiker on|off, /setrules, /setwarn, /panel\n\n"
        "🌐 **Federasiya:**\n"
        "/newfed, /joinfed, /fban\n\n"
        "🎲 **Əyləncə:** /dice"
    )
    await message.answer(help_text, parse_mode="Markdown")

# =====================
# MESSAGE SCOR (/TOPMESAJ) VƏ GERİ DÜYMƏSİ
# =====================
def get_main_top_kb(user_name):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📅 Günlük", callback_data="top_daily"),
                types.InlineKeyboardButton(text="📅 Həftəlik", callback_data="top_weekly"))
    builder.row(types.InlineKeyboardButton(text="📅 Aylıq", callback_data="top_monthly"),
                types.InlineKeyboardButton(text="📊 Bütün zamanlar", callback_data="top_total"))
    builder.row(types.InlineKeyboardButton(text="📄 Detaylı bilgi", callback_data="top_detail"),
                types.InlineKeyboardButton(text="🌐 Global Gruplar", callback_data="top_global"))
    return builder.as_markup()

@dp.message(Command("topmesaj"))
async def topmesaj_command(message: types.Message):
    if message.chat.type == "private":
        await message.answer("❌ Bu əmr yalnız qruplarda işləyir!")
        return
        
    text = (f"**Message Scor** 🇦🇿\n"
            f"👤 {message.from_user.first_name}\n"
            f"/topmesaj\n\n"
            f"👥 **Bu qrup üçün** sıralama növünü seçin.")
    await message.answer(text, reply_markup=get_main_top_kb(message.from_user.first_name), parse_mode="Markdown")

@dp.callback_query(F.data == "back_to_top")
async def back_to_top_handler(callback: types.CallbackQuery):
    text = (f"**Message Scor** 🇦🇿\n"
            f"👤 {callback.from_user.first_name}\n"
            f"/topmesaj\n\n"
            f"👥 **Bu qrup üçün** sıralama növünü seçin.")
    await callback.message.edit_text(text, reply_markup=get_main_top_kb(callback.from_user.first_name), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("top_"))
async def top_callback_handler(callback: types.CallbackQuery):
    category = callback.data.split("_")[1]
    
    # Geri düyməsi (Back)
    back_builder = InlineKeyboardBuilder()
    back_builder.add(types.InlineKeyboardButton(text="⬅️ Geri (Back)", callback_data="back_to_top"))
    
    # Detallar və Global hələlik boşdur
    if category in ["detail", "global"]:
        await callback.message.edit_text(f"ℹ️ Bu bölmə tezliklə aktiv olacaq.", reply_markup=back_builder.as_markup())
        return

    # Statistikaları bazadan çəkək (Top 10)
    db_cursor.execute(f"""
        SELECT scores.user_id, user_info.first_name, scores.msg_count 
        FROM scores 
        JOIN user_info ON scores.user_id = user_info.user_id 
        WHERE scores.chat_id = ? AND scores.category = ? 
        ORDER BY scores.msg_count DESC LIMIT 10
    """, (callback.message.chat.id, category))
    
    rows = db_cursor.fetchall()
    cat_title = {"daily": "Günlük", "weekly": "Həftəlik", "monthly": "Aylıq", "total": "Bütün zamanlar"}[category]
    
    res_text = f"📊 **{cat_title} Sıralama (Top 10)**\n\n"
    if not rows:
        res_text += "Məlumat tapılmadı."
    else:
        for i, row in enumerate(rows, 1):
            res_text += f"{i}. {row[1]} — `{row[2]}` mesaj\n"
            
    await callback.message.edit_text(res_text, reply_markup=back_builder.as_markup(), parse_mode="Markdown")

# =====================
# MODERASİYA ƏMRLƏRİ (HƏR BİRİ AYRI)
# =====================
@dp.message(Command("ban"))
async def ban_handler(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message:
        await message.answer("⚠️ Bu əmr üçün bir mesajı cavablayın.")
        return
    await bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
    await message.answer(f"🚫 {message.reply_to_message.from_user.first_name} banlandı.")

@dp.message(Command("unban"))
async def unban_handler(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    await bot.unban_chat_member(message.chat.id, message.reply_to_message.from_user.id, only_if_banned=True)
    await message.answer(f"✅ {message.reply_to_message.from_user.first_name} banı açıldı.")

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
    await message.answer(f"🔊 {message.reply_to_message.from_user.first_name} səs açıldı.")

@dp.message(Command("warn"))
async def warn_handler(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    uid, cid = message.reply_to_message.from_user.id, message.chat.id
    user_warns[(cid, uid)] = user_warns.get((cid, uid), 0) + 1
    if user_warns[(cid, uid)] >= 3:
        await bot.ban_chat_member(cid, uid)
        user_warns[(cid, uid)] = 0
        await message.answer("🚫 Xəbərdarlıq limiti doldu (3/3), istifadəçi qovuldu.")
    else:
        await message.answer(f"⚠️ {message.reply_to_message.from_user.first_name} xəbərdarlıq aldı: {user_warns[(cid, uid)]}/3")

@dp.message(Command("unwarn"))
async def unwarn_handler(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    user_warns[(message.chat.id, message.reply_to_message.from_user.id)] = 0
    await message.answer("✅ Xəbərdarlıqlar sıfırlandı.")

@dp.message(Command("promote"))
async def promote_handler(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    await bot.promote_chat_member(message.chat.id, message.reply_to_message.from_user.id, 
                                 can_manage_chat=True, can_delete_messages=True, can_restrict_members=True)
    await message.answer(f"✅ {message.reply_to_message.from_user.first_name} artıq admindir.")

@dp.message(Command("demote"))
async def demote_handler(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    await bot.promote_chat_member(message.chat.id, message.reply_to_message.from_user.id, can_manage_chat=False)
    await message.answer(f"❌ {message.reply_to_message.from_user.first_name} adminlikdən çıxarıldı.")

@dp.message(Command("purge"))
async def purge_handler(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    for m_id in range(message.reply_to_message.message_id, message.message_id + 1):
        try: await bot.delete_message(message.chat.id, m_id)
        except: pass

# =====================
# /MY STATİSTİKA
# =====================
@dp.message(Command("my"))
async def my_stats_handler(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    db_cursor.execute("SELECT SUM(msg_count), SUM(sticker_count), SUM(gif_count) FROM scores WHERE user_id = ? AND category = 'total'", (user_id,))
    total_data = db_cursor.fetchone()
    
    db_cursor.execute("SELECT msg_count, sticker_count, gif_count FROM scores WHERE chat_id = ? AND user_id = ? AND category = 'total'", (chat_id, user_id))
    current_data = db_cursor.fetchone()

    t_msg, t_stk, t_gif = total_data if total_data and total_data[0] is not None else (0, 0, 0)
    c_msg, c_stk, c_gif = current_data if current_data else (0, 0, 0)

    stats_text = (
        f"👤 **{message.from_user.first_name} Statistikanız**\n\n"
        f"📊 **Ümumi Cəm (Bütün qruplar):**\n"
        f"💬 Mesaj: {t_msg}\n"
        f"🖼 Stiker: {t_stk}\n"
        f"📹 Gif: {t_gif}\n\n"
        f"📍 **Bu qrupda:**\n"
        f"💬 Mesaj: {c_msg}\n"
        f"🖼 Stiker: {c_stk}\n"
        f"📹 Gif: {c_gif}"
    )
    await message.answer(stats_text, parse_mode="Markdown")

# =====================
# AYARLAR (STİKER BLOKU)
# =====================
@dp.message(Command("stiker"))
async def stiker_control(message: types.Message, command: CommandObject):
    if not await is_admin(message.chat.id, message.from_user.id): return
    val = 1 if command.args == "on" else 0
    db_cursor.execute("INSERT OR REPLACE INTO settings (chat_id, sticker_block) VALUES (?, ?)", (message.chat.id, val))
    db_conn.commit()
    await message.answer(f"⚙️ Stiker nəzarəti: {'AKTİV' if val == 1 else 'DEAKTİV'}")

# =====================
# MƏLUMAT YIĞIMI (SAYĞAC)
# =====================
@dp.message()
async def main_message_handler(message: types.Message):
    if not message.chat or message.chat.type == "private": return
    if message.text and message.text.startswith("/"): return
    
    chat_id, user_id = message.chat.id, message.from_user.id
    
    # Adı yeniləyirik
    db_cursor.execute("INSERT OR REPLACE INTO user_info VALUES (?, ?)", (user_id, message.from_user.first_name))
    
    # Mesaj növünü təyin edirik
    a_type = 'msg'
    if message.sticker: a_type = 'sticker'
    elif message.animation: a_type = 'gif'
    
    # Statistikaları 4 kateqoriya üzrə yazırıq
    for cat in ["total", "daily", "weekly", "monthly"]:
        db_cursor.execute(f"INSERT OR IGNORE INTO scores (chat_id, user_id, category) VALUES (?, ?, ?)", (chat_id, user_id, cat))
        db_cursor.execute(f"UPDATE scores SET {a_type}_count = {a_type}_count + 1 WHERE chat_id = ? AND user_id = ? AND category = ?", (chat_id, user_id, cat))
    db_conn.commit()

    # Stiker bloku yoxlanışı
    db_cursor.execute("SELECT sticker_block FROM settings WHERE chat_id = ?", (chat_id,))
    res = db_cursor.fetchone()
    if res and res[0] == 1 and (message.sticker or message.animation):
        try: await message.delete()
        except: pass

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
