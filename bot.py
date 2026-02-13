import asyncio
import sqlite3
import re
from datetime import datetime

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, ChatPermissions

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
    cursor.execute('''CREATE TABLE IF NOT EXISTS scores (chat_id INTEGER, user_id INTEGER, kateqoriya TEXT, msg_sayi INTEGER DEFAULT 0, PRIMARY KEY (chat_id, user_id, kateqoriya))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_info (user_id INTEGER PRIMARY KEY, first_name TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings (chat_id INTEGER PRIMARY KEY, stiker_bloku INTEGER DEFAULT 0)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS warns (chat_id INTEGER, user_id INTEGER, say INTEGER DEFAULT 0, PRIMARY KEY (chat_id, user_id))''')
    connection.commit()
    return connection, cursor

db_conn, db_cursor = init_db()

# ==========================================================
# 🛡️ YETKİ VƏ İCAZƏ YOXLANIŞLARI
# ==========================================================
async def check_permissions(message: types.Message):
    user_member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if user_member.status not in ("administrator", "creator") and message.from_user.id != OWNER_ID:
        await message.answer("⚠️ Sizin bu əmri istifadə etmək üçün icazəniz yoxdur!")
        return False
    
    bot_member = await bot.get_chat_member(message.chat.id, (await bot.get_me()).id)
    if bot_member.status != "administrator" or not bot_member.can_restrict_members:
        await message.answer("⚠️ Mənim kifayət qədər yetkim yoxdur (Admin deyiləm və ya Ban yetkim yoxdur)!")
        return False
    return True

# ==========================================================
# 👋 START VƏ HELP
# ==========================================================
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    welcome_text = (
        "🤖 Flower-Security Qrup idarə Botu\n\n"
        "🛡️ İmkanlar:\n"
        "• Link / Stiker / GIF avtomatik nəzarət\n"
        "• `/ban`, `/mute`, `/warn` (3/3 Ban sistemi)\n"
        "• `/topmesaj` reytinq və `/my` statistika\n"
        "• 🎲 Əyləncəli animasiyalı oyunlar\n\n"
        "👮 **Botu qrupa əlavə edib admin yetkisi verin.**\n"
        "ℹ️ Əmrlərin siyahısı üçün `/help` yazın."
    )
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="➕ Botu Qrupa Əlavə Et", url=f"https://t.me/Miss_Flower_bot?startgroup=true"))
    builder.row(InlineKeyboardButton(text="📢 Kanal", url="https://t.me/ht_bots"), InlineKeyboardButton(text="💬 Dəstək", url="https://t.me/ht_bots_chat"))
    builder.row(InlineKeyboardButton(text="👤 Developer", url=f"tg://user?id={OWNER_ID}"))
    await message.answer(welcome_text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.message(Command("help"))
async def help_handler(message: types.Message):
    help_text = (
        "❓ Kömək Menyusu\n\n"
        "👮 Admin: /ban, /mute, /unmute, /warn, /unwarn, /stiker on|off\n"
        "📊 Stat: /topmesaj, /my\n"
        "🎲 Oyun: /dice, /slot, /basket, /dart, /futbol"
    )
    await message.answer(help_text, parse_mode="Markdown")

# ==========================================================
# 👮 ADMIN ƏMRLƏRİ
# ==========================================================
@dp.message(Command("ban"))
async def ban_handler(message: types.Message):
    if not await check_permissions(message): return
    if not message.reply_to_message: return await message.answer("⚠️ Ban etmək üçün istifadəçini cavablayın.")
    try:
        await bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
        await message.answer(f"🚫 {message.reply_to_message.from_user.first_name} qrupdan qovuldu.")
    except: await message.answer("❌ Xəta: Admini ban etmək olmaz.")

@dp.message(Command("mute"))
async def mute_handler(message: types.Message):
    if not await check_permissions(message): return
    if not message.reply_to_message: return await message.answer("⚠️ Səssizə almaq üçün cavablayın.")
    try:
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, permissions=ChatPermissions(can_send_messages=False))
        await message.answer(f"🔇 {message.reply_to_message.from_user.first_name} səssizə alındı.")
    except: pass

@dp.message(Command("unmute"))
async def unmute_handler(message: types.Message):
    if not await check_permissions(message): return
    if not message.reply_to_message: return await message.answer("⚠️ Səsi açmaq üçün cavablayın.")
    try:
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, permissions=ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True))
        await message.answer(f"🔊 {message.reply_to_message.from_user.first_name} səsi açıldı.")
    except: pass

@dp.message(Command("warn"))
async def warn_handler(message: types.Message):
    if not await check_permissions(message): return
    if not message.reply_to_message: return await message.answer("⚠️ Xəbərdarlıq üçün cavablayın.")
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
    if not await check_permissions(message): return
    if not message.reply_to_message: return await message.answer("⚠️ İstifadəçini cavablayın.")
    db_cursor.execute("UPDATE warns SET say = 0 WHERE chat_id = ? AND user_id = ?", (message.chat.id, message.reply_to_message.from_user.id))
    db_conn.commit()
    await message.answer("✅ Xəbərdarlıqlar təmizləndi.")

# ==========================================================
# 📊 REYTİNQ VƏ OYUNLAR
# ==========================================================
@dp.message(Command("my"))
async def my_stats(message: types.Message):
    u_id, c_id = message.from_user.id, (message.chat.id if message.chat.type != "private" else 0)
    db_cursor.execute("SELECT msg_sayi FROM scores WHERE user_id = ? AND chat_id = ? AND kateqoriya = 'ümumi'", (u_id, c_id))
    res = db_cursor.fetchone()
    say = res[0] if res else 0
    await message.answer(f"👤 İstifadəçi: {message.from_user.first_name}\n📊 **Ümumi mesajınız:** {say}")

@dp.message(Command("topmesaj"))
async def top_cmd(message: types.Message):
    if message.chat.type == "private": return
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📅 Günlük", callback_data="top_günlük"), InlineKeyboardButton(text="📅 Həftəlik", callback_data="top_həftəlik"))
    builder.row(InlineKeyboardButton(text="📅 Aylıq", callback_data="top_aylıq"), InlineKeyboardButton(text="📊 Ümumi", callback_data="top_ümumi"))
    await message.answer("📊 Reytinq Menyusu", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("top_"))
async def process_top(callback: types.CallbackQuery):
    kat = callback.data.split("_")[1]
    db_cursor.execute(f"SELECT user_info.first_name, scores.msg_sayi FROM scores JOIN user_info ON scores.user_id = user_info.user_id WHERE scores.chat_id = ? AND scores.kateqoriya = ? ORDER BY scores.msg_sayi DESC LIMIT 10", (callback.message.chat.id, kat))
    rows = db_cursor.fetchall()
    res = f"📊 {kat.capitalize()} Reytinq:\n\n"
    if not rows: res += "Məlumat yoxdur."
    else:
        for i, r in enumerate(rows, 1): res += f"{i}. {r[0]} — {r[1]} mesaj\n"
    await callback.message.edit_text(res, reply_markup=callback.message.reply_markup)

@dp.message(Command("dice", "slot", "basket", "dart", "futbol"))
async def games_handler(message: types.Message):
    emojis = {"dice": "🎲", "slot": "🎰", "basket": "🏀", "dart": "🎯", "futbol": "⚽"}
    cmd = message.text.split()[0][1:]
    await message.answer_dice(emoji=emojis.get(cmd, "🎲"))

# ==========================================================
# 🛡️ STİKER KOMANDASI (YALNIZ OWNER VƏ CREATOR)
# ==========================================================
@dp.message(Command("stiker"))
async def stiker_settings(message: types.Message, command: CommandObject):
    user_member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    # Yalnız Qurucu (Creator) və Bot Sahibi (Owner) dəyişə bilər
    if user_member.status != "creator" and message.from_user.id != OWNER_ID:
        return await message.answer("⚠️ Bu tənzimləməni yalnız qrup sahibi dəyişə bilər!")
    
    val = 1 if command.args == "off" else 0
    db_cursor.execute("INSERT OR REPLACE INTO settings (chat_id, stiker_bloku) VALUES (?, ?)", (message.chat.id, val))
    db_conn.commit()
    await message.answer("🚫 Stiker və Gif bloku aktiv edildi." if val else "🔓 Stiker və gif bloku deaktiv edildi.")

# ==========================================================
# 🛡️ LİNK / STİKER SİLMƏ VƏ SAYĞAC
# ==========================================================
@dp.message()
async def global_handler(message: types.Message):
    if not message.chat or message.chat.type == "private": return
    u_id, c_id = message.from_user.id, message.chat.id
    user_member = await bot.get_chat_member(c_id, u_id)
    is_admin = user_member.status in ("administrator", "creator") or u_id == OWNER_ID

    # 1. LİNK SİLMƏ
    if not is_admin and message.entities:
        for entity in message.entities:
            if entity.type in ["url", "text_link"] or (message.text and ("t.me/" in message.text or "http" in message.text)):
                try: return await message.delete()
                except: pass

    # 2. STİKER VƏ GİF SİLMƏ (ƏVVƏLKİ KİMİ STABİL)
    db_cursor.execute("SELECT stiker_bloku FROM settings WHERE chat_id = ?", (c_id,))
    s = db_cursor.fetchone()
    if s and s[0] == 1 and not is_admin:
        if message.sticker or message.animation:
            try: return await message.delete()
            except: pass

    # 3. SAYĞAC VƏ MƏLUMAT YENİLƏMƏ
    db_cursor.execute("INSERT OR REPLACE INTO user_info VALUES (?, ?)", (u_id, message.from_user.first_name))
    if not (message.text and message.text.startswith("/")):
        for k in ["günlük", "həftəlik", "aylıq", "ümumi"]:
            db_cursor.execute(f"INSERT OR IGNORE INTO scores (chat_id, user_id, kateqoriya) VALUES (?, ?, ?)", (c_id, u_id, k))
            db_cursor.execute(f"UPDATE scores SET msg_sayi = msg_sayi + 1 WHERE chat_id = ? AND user_id = ? AND kateqoriya = ?", (c_id, u_id, k))
        db_conn.commit()

# ==========================================================
# 🕒 AVTOMATİK SIFIRLAMA TAYMERİ
# ==========================================================
async def reset_timer():
    while True:
        now = datetime.now()
        if now.hour == 0 and now.minute == 0:
            db_cursor.execute("UPDATE scores SET msg_sayi = 0 WHERE kateqoriya = 'günlük'")
            if now.weekday() == 0: db_cursor.execute("UPDATE scores SET msg_sayi = 0 WHERE kateqoriya = 'həftəlik'")
            if now.day == 1: db_cursor.execute("UPDATE scores SET msg_sayi = 0 WHERE kateqoriya = 'aylıq'")
            db_conn.commit()
            await asyncio.sleep(60)
        await asyncio.sleep(30)

async def main():
    asyncio.create_task(reset_timer())
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__": asyncio.run(main())
