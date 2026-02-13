import asyncio
import os
import sqlite3
import logging
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ==========================================================
# 🛡️ FLOWER-SECURITY KONFİQURASİYA HİSSƏSİ
# ==========================================================

# Botun sahibi (Sənin ID-n)
OWNER_ID = 8024893255

# @BotFather-dən aldığın tokeni bura dırnaq arasına yaz:
API_TOKEN = "TOKENI_BURA_YAZ"

# Bot və Dispatcher obyektlərinin yaradılması
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Loqların tənzimlənməsi (Xətaları görmək üçün)
logging.basicConfig(level=logging.INFO)

# ==========================================================
# 📊 SQLITE MƏLUMAT BAZASI (TAM VƏ GENİŞ)
# ==========================================================

db_conn = sqlite3.connect("flower_security.db")
db_cursor = db_conn.cursor()

# 1. Message Scor (Reytinq) Cədvəli
# Hər qrup və hər istifadəçi üçün kateqoriya üzrə statistikalar
db_cursor.execute('''
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

# 2. İstifadəçi Adları Cədvəli
# Reytinqdə adların düzgün görünməsi üçün
db_cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_info (
        user_id INTEGER PRIMARY KEY, 
        first_name TEXT
    )
''')

# 3. Qrup Tənzimləmələri (Stiker bloku və s.)
db_cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        chat_id INTEGER PRIMARY KEY, 
        sticker_block INTEGER DEFAULT 0
    )
''')

# 4. Xəbərdarlıq Sistemi (Warn)
db_cursor.execute('''
    CREATE TABLE IF NOT EXISTS warns (
        chat_id INTEGER, 
        user_id INTEGER, 
        count INTEGER DEFAULT 0, 
        PRIMARY KEY (chat_id, user_id)
    )
''')

db_conn.commit()

# ==========================================================
# 🛠️ KÖMƏKÇİ FUNKSİYALAR (ADMİN YOXLANIŞI VƏ VAXT)
# ==========================================================

async def is_admin(chat_id: int, user_id: int):
    """İstifadəçinin admin və ya owner olduğunu yoxlayır"""
    if user_id == OWNER_ID:
        return True
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        if member.status in ("administrator", "creator"):
            return True
        return False
    except Exception:
        return False

async def is_creator_or_owner(chat_id: int, user_id: int):
    """İstifadəçinin qrup yaradıcısı və ya owner olduğunu yoxlayır"""
    if user_id == OWNER_ID:
        return True
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        if member.status == "creator":
            return True
        return False
    except Exception:
        return False

def parse_time(time_string: str):
    """Vaxtı (10m, 1h, 1d) saniyələrə çevirir"""
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

# ==========================================================
# 👮 MODERASİYA VƏ ADMİN KOMANDALARI (HƏR BİRİ AYRI)
# ==========================================================

# /admin - İstifadəçini admin edir
@dp.message(Command("admin"))
async def cmd_promote_user(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        await message.answer("⚠️ Admin etmək üçün istifadəçinin mesajını cavablayın (reply).")
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
        await message.answer(f"✅ {message.reply_to_message.from_user.first_name} artıq admindir!")
    except Exception as e:
        await message.answer(f"❌ Xəta baş verdi: {e}")

# /unadmin - Adminlikdən çıxarır
@dp.message(Command("unadmin"))
async def cmd_demote_user(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        return
    
    try:
        await bot.promote_chat_member(
            chat_id=message.chat.id,
            user_id=message.reply_to_message.from_user.id,
            can_manage_chat=False
        )
        await message.answer(f"❌ {message.reply_to_message.from_user.first_name} adminlikdən çıxarıldı.")
    except Exception:
        pass

# /ban - İstifadəçini ban edir
@dp.message(Command("ban"))
async def cmd_ban_user(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        return
    
    try:
        await bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
        await message.answer(f"🚫 {message.reply_to_message.from_user.first_name} qrupdan banlandı.")
    except Exception:
        await message.answer("❌ İstifadəçini banlamaq mümkün olmadı.")

# /unban - Banı açır
@dp.message(Command("unban"))
async def cmd_unban_user(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        return
    
    await bot.unban_chat_member(message.chat.id, message.reply_to_message.from_user.id, only_if_banned=True)
    await message.answer(f"✅ {message.reply_to_message.from_user.first_name} istifadəçisinin banı açıldı.")

# /mute - Səssizə alır (Nümunə: /mute 10m)
@dp.message(Command("mute"))
async def cmd_mute_user(message: types.Message, command: CommandObject):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        return
    
    delta = parse_time(command.args) if command.args else None
    until = datetime.now() + delta if delta else None
    
    try:
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=message.reply_to_message.from_user.id,
            permissions=types.ChatPermissions(can_send_messages=False),
            until_date=until
        )
        time_text = f" {command.args} müddətinə" if command.args else ""
        await message.answer(f"🔇 {message.reply_to_message.from_user.first_name}{time_text} səssizə alındı.")
    except Exception:
        await message.answer("❌ İstifadəçini səssizə almaq olmadı.")

# /unmute - Səsi açır
@dp.message(Command("unmute"))
async def cmd_unmute_user(message: types.Message):
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
            can_send_other_messages=True,
            can_add_web_page_previews=True
        )
    )
    await message.answer(f"🔊 {message.reply_to_message.from_user.first_name} artıq danışa bilər.")

# /warn - Xəbərdarlıq sistemi
@dp.message(Command("warn"))
async def cmd_warn_user(message: types.Message):
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
        await message.answer(f"🚫 {message.reply_to_message.from_user.first_name} 3 xəbərdarlıq dolduğu üçün banlandı.")
    else:
        await message.answer(f"⚠️ {message.reply_to_message.from_user.first_name} xəbərdarlıq aldı: {current_warns}/3")

# /purge - Mesajları təmizləyir
@dp.message(Command("purge"))
async def cmd_purge_messages(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        await message.answer("⚠️ Təmizləməyə başlamaq üçün bir mesajı cavablayın.")
        return
    
    start_id = message.reply_to_message.message_id
    end_id = message.message_id
    
    count = 0
    for msg_id in range(start_id, end_id + 1):
        try:
            await bot.delete_message(message.chat.id, msg_id)
            count += 1
        except Exception:
            continue
    
    status_msg = await message.answer(f"✅ {count} mesaj təmizləndi.")
    await asyncio.sleep(3)
    try:
        await status_msg.delete()
    except:
        pass

# ==========================================================
# 📊 MESSAGE SCOR (REYTİNQ SİSTEMİ)
# ==========================================================

def get_score_keyboard():
    """Skrinşotdakı düymələrin tam siyahısı"""
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📅 Günlük", callback_data="score_daily"),
                types.InlineKeyboardButton(text="📅 Həftəlik", callback_data="score_weekly"),
                types.InlineKeyboardButton(text="📅 Aylıq", callback_data="score_monthly"))
    builder.row(types.InlineKeyboardButton(text="📊 Bütün zamanlarda", callback_data="score_total"))
    builder.row(types.InlineKeyboardButton(text="📄 Detaylı bilgi", callback_data="score_detail"),
                types.InlineKeyboardButton(text="🌐 Global Gruplar", callback_data="score_global"))
    return builder.as_markup()

@dp.message(Command("topmesaj"))
async def cmd_topmesaj(message: types.Message):
    if message.chat.type == "private":
        return
    
    text = (
        f"📊 **Message Scor** 🇦🇿\n"
        f"👤 {message.from_user.first_name}\n\n"
        f"👥 **Bu qrup üçün** sıralama növünü seçin."
    )
    await message.answer(text, reply_markup=get_score_keyboard(), parse_mode="Markdown")

@dp.callback_query(F.data == "score_back")
async def cb_score_back(callback: types.CallbackQuery):
    text = (
        f"📊 **Message Scor** 🇦🇿\n"
        f"👤 {callback.from_user.first_name}\n\n"
        f"👥 **Bu qrup üçün** sıralama növünü seçin."
    )
    await callback.message.edit_text(text, reply_markup=get_score_keyboard(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("score_"))
async def cb_process_scores(callback: types.CallbackQuery):
    category = callback.data.split("_")[1]
    
    if category in ["detail", "global"]:
        await callback.answer("ℹ️ Bu funksiya tezliklə aktiv olacaq!", show_alert=True)
        return

    # Məlumatları bazadan çək
    db_cursor.execute(f"""
        SELECT scores.user_id, user_info.first_name, scores.msg_count 
        FROM scores 
        JOIN user_info ON scores.user_id = user_info.user_id 
        WHERE scores.chat_id = ? AND scores.category = ? 
        ORDER BY scores.msg_count DESC LIMIT 10
    """, (callback.message.chat.id, category))
    
    rows = db_cursor.fetchall()
    titles = {"daily": "Günlük", "weekly": "Həftəlik", "monthly": "Aylıq", "total": "Ümumi"}
    
    res_text = f"📊 **{titles[category]} Sıralama (Top 10)**\n\n"
    if not rows:
        res_text += "Heç bir aktivlik tapılmadı."
    else:
        for i, row in enumerate(rows, 1):
            res_text += f"{i}. {row[1]} — `{row[2]}` mesaj\n"
    
    back_kb = InlineKeyboardBuilder()
    back_kb.add(types.InlineKeyboardButton(text="⬅️ Geri Qayıt", callback_data="score_back"))
    await callback.message.edit_text(res_text, reply_markup=back_kb.as_markup(), parse_mode="Markdown")

# ==========================================================
# 🛡️ STİKER BLOKU (TƏRS MƏNTİQ)
# ==========================================================

@dp.message(Command("stiker"))
async def cmd_stiker_control(message: types.Message, command: CommandObject):
    if not await is_creator_or_owner(message.chat.id, message.from_user.id):
        return
    
    # Sənin istədiyin: /stiker off -> BLOK AKTİV (1), /stiker on -> İCAZƏ (0)
    if command.args == "off":
        db_cursor.execute("INSERT OR REPLACE INTO settings (chat_id, sticker_block) VALUES (?, 1)", (message.chat.id,))
        db_conn.commit()
        await message.answer("🛡️ Stiker bloku AKTİV edildi (Stikerlər silinəcək).")
    elif command.args == "on":
        db_cursor.execute("INSERT OR REPLACE INTO settings (chat_id, sticker_block) VALUES (?, 0)", (message.chat.id,))
        db_conn.commit()
        await message.answer("🔓 Stiker bloku DEAKTİV edildi (Stikerlərə icazə verilir).")
    else:
        await message.answer("ℹ️ İstifadə: `/stiker off` (bloklamaq) və ya `/stiker on` (icazə vermək)")

# ==========================================================
# ⚙️ QLOBAL HANDLER (HƏR MESAJI SAYMAQ VƏ SİLMƏK)
# ==========================================================

@dp.message()
async def global_message_handler(message: types.Message):
    # Şəxsi mesajlarda (DM) sayğac işləməsin
    if not message.chat or message.chat.type == "private":
        return
    
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # İstifadəçi adını yenilə (Reytinqdə ID görünməsin deyə)
    db_cursor.execute("INSERT OR REPLACE INTO user_info (user_id, first_name) VALUES (?, ?)", (user_id, message.from_user.first_name))
    
    # Əmrləri sayğaca daxil etmirik
    if message.text and message.text.startswith("/"):
        return
    
    # Tipini təyin et
    m_type = 'msg'
    if message.sticker:
        m_type = 'sticker'
    elif message.animation: # GIF-lər animation sayılır
        m_type = 'gif'
    
    # 4 kateqoriya üzrə sayğacı artır
    for cat in ["daily", "weekly", "monthly", "total"]:
        db_cursor.execute(f"INSERT OR IGNORE INTO scores (chat_id, user_id, category) VALUES (?, ?, ?)", (chat_id, user_id, cat))
        db_cursor.execute(f"UPDATE scores SET {m_type}_count = {m_type}_count + 1 WHERE chat_id = ? AND user_id = ? AND category = ?", (chat_id, user_id, cat))
    
    db_conn.commit()

    # --- STİKER BLOKU YOXLANIŞI ---
    db_cursor.execute("SELECT sticker_block FROM settings WHERE chat_id = ?", (chat_id,))
    res = db_cursor.fetchone()
    
    if res and res[0] == 1: # Əgər /stiker off yazılıb bloklanıbsa
        if message.sticker or message.animation:
            try:
                await message.delete()
            except Exception:
                pass

# ==========================================================
# 🚀 BOTU BAŞLATMA HİSSƏSİ
# ==========================================================

async def main():
    print("Flower-Security Bot işə düşdü...")
    # Polling başlat
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot dayandırıldı.")
