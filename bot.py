import asyncio
import sqlite3
import re
from datetime import datetime

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, ChatPermissions

# ==========================================================
# 1. KONFİQURASİYA VƏ SÖYÜŞ BAZASI
# ==========================================================
OWNER_ID = 8024893255
API_TOKEN = "7886882115:AAEodWPGRhT6CQ-1rQgHy4ZKL_3wkKENe8Q"

SOYUS_LISTESI = [
    "gijdillağ", "peyser", "peysər", "bicbala", "ogras", "serefsiz", "alçaq",
    "exlaqsiz", "got", "amciq", "dausaq", "sik", "dashaq", "memesi", "götveren",
    "götvərən", "peysər", "gicdillaq", "oğraş", "şərəfsiz", "əxlaqsız", "qush",
    "gic", "var yox", "nesil necebe", "ananin", "bacinin", "atavin", "var-yox",
    "qancıq", "biçbala", "oğraş", "sikiş", "amcıq", "daşşaq", "götün", "peysərsən"
]

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# ==========================================================
# 2. MƏLUMAT BAZASI
# ==========================================================
def init_db():
    connection = sqlite3.connect("flower_security_ultra.db")
    cursor = connection.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS scores (chat_id INTEGER, user_id INTEGER, kateqoriya TEXT, msg_sayi INTEGER DEFAULT 0, PRIMARY KEY (chat_id, user_id, kateqoriya))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_info (user_id INTEGER PRIMARY KEY, first_name TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings (chat_id INTEGER PRIMARY KEY, stiker_bloku INTEGER DEFAULT 0, welcome_msg TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS warns (chat_id INTEGER, user_id INTEGER, say INTEGER DEFAULT 0, PRIMARY KEY (chat_id, user_id))''')
    connection.commit()
    return connection, cursor

db_conn, db_cursor = init_db()

# ==========================================================
# 3. YETKİ YOXLANIŞI (ROSE STYLE)
# ==========================================================
async def check_permissions(message: types.Message):
    # Şəxsi çat yoxlanışı (Tələb etdiyin qoruma)
    if message.chat.type == "private":
        await message.answer("⚠️ Bu komut qruplar üçündür!")
        return False
        
    user_member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if user_member.status not in ("administrator", "creator") and message.from_user.id != OWNER_ID:
        await message.answer("Sizin bu komandanı icra etmək üçün lazımi icazəniz yoxdur.")
        return False
    return True

async def check_bot_permissions(message: types.Message):
    bot_member = await bot.get_chat_member(message.chat.id, (await bot.get_me()).id)
    if bot_member.status != "administrator":
        await message.answer("Səhv: Mənim bu istifadəçini idarə etmək üçün kifayət qədər səlahiyyətim yoxdur.")
        return False
    return True

# ==========================================================
# 4. START VƏ HELP
# ==========================================================
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    welcome_text = (
        "🤖 Flower-Security Qrup idarə Botu\n\n"
        "🛡️ İmkanlar:\n"
        "• Link / Stiker / Söyüş avtomatik nəzarət\n"
        "• /ban, /unban, /mute, /unmute, /warn (3/3 sistemi)\n"
        "• /top reytinq və /my statistika\n"
        "• 🎲 Əyləncəli animasiyalı oyunlar\n\n"
        "👮 Botu qrupa əlavə edib admin yetkisi verin.\n"
        "ℹ️ Əmrlərin siyahısı üçün /help yazın."
    )
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="➕ Botu Qrupa Əlavə Et", url=f"https://t.me/Miss_Flower_bot?startgroup=true"))
    builder.row(InlineKeyboardButton(text="📢 Kanal", url="https://t.me/ht_bots"), InlineKeyboardButton(text="💬 Dəstək", url="https://t.me/ht_bots_chat"))
    builder.row(InlineKeyboardButton(text="🧑‍💻 Developer", url=f"tg://user?id={OWNER_ID}"))
    await message.answer(welcome_text, reply_markup=builder.as_markup())

@dp.message(Command("help"))
async def help_handler(message: types.Message):
    help_text = (
        "❓ Kömək Menyusu\n\n"
        "👮 Admin: /ban, /unban, /mute, /unmute, /warn, /unwarn, /stiker on|off\n"
        "👋 Qarşılama: /setwelcome [mesaj] - (Qrup admini tərəfindən)\n"
        "📊 Stat: /top, /my\n"
        "🎲 Oyun: /dice, /slot, /basket, /dart, /futbol"
    )
    await message.answer(help_text)

# ==========================================================
# YENİ: QURUCU ÜÇÜN LEAVE ƏMRİ (ŞƏXSİDƏ İŞLƏYİR)
# ==========================================================
@dp.message(Command("leave"))
async def owner_leave_handler(message: types.Message, command: CommandObject):
    if message.from_user.id != OWNER_ID:
        return # Qurucu deyilsə heç nə etmə
        
    if not command.args:
        return await message.answer("Nümunə: `/leave -100123456789`", parse_mode="Markdown")

    chat_id = command.args
    try:
        await bot.leave_chat(chat_id)
        await message.answer(f"✅ Bot uğurla qrupdan çıxarıldı: {chat_id}")
    except Exception as e:
        await message.answer(f"❌ Xəta baş verdi: {e}")

# ==========================================================
# 5. ADMIN ƏMRLƏRİ
# ==========================================================

@dp.message(Command("setwelcome"))
async def set_welcome_handler(message: types.Message, command: CommandObject):
    if not await check_permissions(message): return
    
    u_member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if u_member.status != "creator" and not getattr(u_member, 'can_change_info', False) and message.from_user.id != OWNER_ID:
        return await message.answer("⚠️ Bu əmri istifadə etmək üçün 'Məlumatları dəyişmək' yetkiniz olmalıdır!")

    if not command.args:
        return await message.answer("İstifadə: `/setwelcome Xoş gəldin {user}!`\n\nNot: `{user}` yazsanız yeni gələnin adını qeyd edərəm.")

    welcome_msg = command.args
    db_cursor.execute("INSERT INTO settings (chat_id, welcome_msg) VALUES (?, ?) ON CONFLICT(chat_id) DO UPDATE SET welcome_msg=excluded.welcome_msg", (message.chat.id, welcome_msg))
    db_conn.commit()
    await message.answer(f"✅ Qarşılama mesajı yadda saxlanıldı:\n\n{welcome_msg}")

@dp.message(Command("ban"))
async def ban_handler(message: types.Message):
    if not await check_permissions(message): return
    if not message.reply_to_message: return await message.answer("İstifadəçi təyin edilməyib. Kimin haqqında danışdığınızı bilmirəm.")
    if not await check_bot_permissions(message): return
    try:
        await bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
        await message.answer(f"🚫 {message.reply_to_message.from_user.first_name} qrupdan qovuldu.")
    except: await message.answer("Səhv: Mənim bu istifadəçini idarə etmək üçün kifayət qədər səlahiyyətim yoxdur.")

@dp.message(Command("unban"))
async def unban_handler(message: types.Message):
    if not await check_permissions(message): return
    if not message.reply_to_message: return await message.answer("İstifadəçi təyin edilməyib. Kimin haqqında danışdığınızı bilmirəm.")
    if not await check_bot_permissions(message): return
    try:
        await bot.unban_chat_member(message.chat.id, message.reply_to_message.from_user.id, only_if_blocked=True)
        await message.answer(f"✅ {message.reply_to_message.from_user.first_name} blokdan çıxarıldı.")
    except: pass

@dp.message(Command("mute"))
async def mute_handler(message: types.Message):
    if not await check_permissions(message): return
    if not message.reply_to_message: return await message.answer("İstifadəçi təyin edilməyib. Kimin haqqında danışdığınızı bilmirəm.")
    if not await check_bot_permissions(message): return
    try:
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, permissions=ChatPermissions(can_send_messages=False))
        await message.answer(f"🔇 {message.reply_to_message.from_user.first_name} səssizə alındı.")
    except: pass

@dp.message(Command("unmute"))
async def unmute_handler(message: types.Message):
    if not await check_permissions(message): return
    if not message.reply_to_message: return await message.answer("İstifadəçi təyin edilməyib. Kimin haqqında danışdığınızı bilmirəm.")
    if not await check_bot_permissions(message): return
    try:
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, permissions=ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True))
        await message.answer(f"🔊 {message.reply_to_message.from_user.first_name} səsi açıldı.")
    except: pass

@dp.message(Command("admin"))
async def admin_handler(message: types.Message):
    if not await check_permissions(message): return
    if not message.reply_to_message: return await message.answer("İstifadəçi təyin edilməyib. Kimin haqqında danışdığınızı bilmirəm.")
    if not await check_bot_permissions(message): return
    try:
        await bot.promote_chat_member(message.chat.id, message.reply_to_message.from_user.id, can_manage_chat=True, can_delete_messages=True, can_restrict_members=True, can_promote_members=True)
        await message.answer(f"Uğurlu: {message.reply_to_message.from_user.first_name} admin təyin edildi.")
    except: await message.answer("Səhv: Mənim bu istifadəçini idarə etmək üçün kifayət qədər səlahiyyətim yoxdur.")

@dp.message(Command("unadmin"))
async def unadmin_handler(message: types.Message):
    if not await check_permissions(message): return
    if not message.reply_to_message: return await message.answer("İstifadəçi təyin edilməyib. Kimin haqqında danışdığınızı bilmirəm.")
    if not await check_bot_permissions(message): return
    try:
        await bot.promote_chat_member(message.chat.id, message.reply_to_message.from_user.id, can_change_info=False, can_delete_messages=False, can_invite_users=False, can_restrict_members=False, can_pin_messages=False, can_promote_members=False, can_manage_chat=False)
        await message.answer(f"Uğurlu: {message.reply_to_message.from_user.first_name} adminlikdən çıxarıldı.")
    except: await message.answer("Səhv: Mənim bu istifadəçini idarə etmək üçün kifayət qədər səlahiyyətim yoxdur.")

@dp.message(Command("warn"))
async def warn_handler(message: types.Message):
    if not await check_permissions(message): return
    if not message.reply_to_message: return await message.answer("İstifadəçi təyin edilməyib. Kimin haqqında danışdığınızı bilmirəm.")
    if not await check_bot_permissions(message): return
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
        await message.answer(f"🚫 {message.reply_to_message.from_user.first_name} 3 xəbərdarlıq dolduğu üçün qovuldu.")
    else: await message.answer(f"⚠️ {message.reply_to_message.from_user.first_name} xəbərdarlıq aldı! Cəmi: {cnt}/3")

@dp.message(Command("unwarn"))
async def unwarn_handler(message: types.Message):
    if not await check_permissions(message): return
    if not message.reply_to_message: return await message.answer("İstifadəçi təyin edilməyib. Kimin haqqında danışdığınızı bilmirəm.")
    db_cursor.execute("UPDATE warns SET say = 0 WHERE chat_id = ? AND user_id = ?", (message.chat.id, message.reply_to_message.from_user.id))
    db_conn.commit()
    await message.answer(f"✅ {message.reply_to_message.from_user.first_name} xəbərdarlıqları təmizləndi.")

# ==========================================================
# 6. /TOP REYTİNQ
# ==========================================================
@dp.message(Command("top"))
async def top_menu(message: types.Message):
    if message.chat.type == "private": 
        return await message.answer("⚠️ Bu komut qruplar üçündür!")
        
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📅 Günlük", callback_data="top_günlük"), 
                InlineKeyboardButton(text="📅 Həftəlik", callback_data="top_həftəlik"),
                InlineKeyboardButton(text="📅 Aylıq", callback_data="top_aylıq"))
    builder.row(InlineKeyboardButton(text="📊 Bütün zamanlarda", callback_data="top_ümumi"))
    
    text = (
        "📊 Mesaj sayğacı 📝\n"
        "------------------\n"
        "👥 Bu qrup üçün sıralama növünü seçin.\n\n"
        f"Bu menyu {message.from_user.first_name} tərəfindən açıldı."
    )
    await message.answer(text, reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("top_"))
async def process_top_callback(callback: types.CallbackQuery):
    kat = callback.data.split("_")[1]
    kat_name = {"günlük": "BUGÜN", "həftəlik": "bu HƏFTƏ", "aylıq": "bu AY", "ümumi": "BÜTÜN ZAMANLARDA"}[kat]
    
    db_cursor.execute(f"SELECT user_info.first_name, scores.msg_sayi FROM scores JOIN user_info ON scores.user_id = user_info.user_id WHERE scores.chat_id = ? AND scores.kateqoriya = ? ORDER BY scores.msg_sayi DESC LIMIT 20", (callback.message.chat.id, kat))
    rows = db_cursor.fetchall()
    
    res = "📊 Mesaj sayğacı\n"
    res += f"👥 bu Qrupda {kat_name} ən çox aktiv olanlar:\n\n"
    res += "İstifadəçi → Mesaj\n"
    
    if not rows:
        res += "Məlumat yoxdur."
    else:
        for i, r in enumerate(rows, 1):
            res += f"🔹 {i}. {r[0]} : {r[1]}\n"
    
    db_cursor.execute("SELECT msg_sayi FROM scores WHERE user_id = ? AND chat_id = ? AND kateqoriya = ?", (callback.from_user.id, callback.message.chat.id, kat))
    own = db_cursor.fetchone()
    res += f"\nSənin Xeyal : {own[0] if own else 0}"
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⬅️ Geri", callback_data="back_to_top"))
    await callback.message.edit_text(res, reply_markup=builder.as_markup())

@dp.callback_query(F.data == "back_to_top")
async def back_to_top(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📅 Günlük", callback_data="top_günlük"), 
                InlineKeyboardButton(text="📅 Həftəlik", callback_data="top_həftəlik"),
                InlineKeyboardButton(text="📅 Aylıq", callback_data="top_aylıq"))
    builder.row(InlineKeyboardButton(text="📊 Bütün zamanlarda", callback_data="top_ümumi"))
    await callback.message.edit_text("📊 Mesaj sayğacı\n\n👥 Sıralama növünü seçin:", reply_markup=builder.as_markup())

# ==========================================================
# 7. DİGƏR KOMANDALAR
# ==========================================================
@dp.message(Command("my"))
async def my_stats(message: types.Message):
    if message.chat.type == "private":
        return await message.answer("⚠️ Bu komut qruplar üçündür!")
        
    u_id = message.from_user.id
    db_cursor.execute("SELECT msg_sayi FROM scores WHERE user_id = ? AND chat_id = ? AND kateqoriya = 'ümumi'", (u_id, message.chat.id))
    res = db_cursor.fetchone()
    await message.answer(f"👤 {message.from_user.first_name}\n📊 Ümumi mesajın: {res[0] if res else 0}")

@dp.message(Command("stiker"))
async def stiker_settings(message: types.Message, command: CommandObject):
    if not await check_permissions(message): return
    
    u_member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if u_member.status != "creator" and message.from_user.id != OWNER_ID:
        return await message.answer("⚠️ Bu tənzimləməni yalnız qrup sahibi dəyişə bilər!")
    
    if command.args == "off":
        db_cursor.execute("INSERT INTO settings (chat_id, stiker_bloku) VALUES (?, 1) ON CONFLICT(chat_id) DO UPDATE SET stiker_bloku=1", (message.chat.id,))
        db_conn.commit()
        await message.answer("🚫 Stiker və gif bloku aktivdir")
    elif command.args == "on":
        db_cursor.execute("INSERT INTO settings (chat_id, stiker_bloku) VALUES (?, 0) ON CONFLICT(chat_id) DO UPDATE SET stiker_bloku=0", (message.chat.id,))
        db_conn.commit()
        await message.answer("🔓 Stiker və gif bloku deaktivdir")

@dp.message(Command("dice", "slot", "basket", "dart", "futbol"))
async def games_handler(message: types.Message):
    if message.chat.type == "private":
        return await message.answer("⚠️ Bu komut qruplar üçündür!")
    emojis = {"dice": "🎲", "slot": "🎰", "basket": "🏀", "dart": "🎯", "futbol": "⚽"}
    cmd = message.text.split()[0][1:]
    await message.answer_dice(emoji=emojis.get(cmd, "🎲"))

# ==========================================================
# 8. GLOBAL HANDLER (QORUMALAR VƏ SAYĞAC)
# ==========================================================
@dp.chat_member()
async def welcome_new_member(event: types.ChatMemberUpdated):
    if event.new_chat_member.status == "member":
        db_cursor.execute("SELECT welcome_msg FROM settings WHERE chat_id = ?", (event.chat.id,))
        res = db_cursor.fetchone()
        if res and res[0]:
            msg = res[0].replace("{user}", event.new_chat_member.user.first_name)
            await bot.send_message(event.chat.id, msg)

@dp.message()
async def global_handler(message: types.Message):
    if not message.chat or message.chat.type == "private": return
    u_id, c_id = message.from_user.id, message.chat.id
    u_member = await bot.get_chat_member(c_id, u_id)
    is_admin = u_member.status in ("administrator", "creator") or u_id == OWNER_ID
    mention = f"[{message.from_user.first_name}](tg://user?id={u_id})"

    # SÖYÜŞ QORUMASI
    if message.text:
        msg_lower = message.text.lower()
        if any(s in msg_lower for s in SOYUS_LISTESI):
            try:
                await message.delete()
                return await message.answer(f"⚠️ {mention}, zəhmət olmasa qrupda normal danışın!", parse_mode="Markdown")
            except: pass

    # LİNK QORUMASI
    if not is_admin:
        has_link = False
        if message.entities:
            for e in message.entities:
                if e.type in ["url", "text_link"]: has_link = True
        if not has_link and message.text and ("t.me/" in message.text or "http" in message.text):
            has_link = True
        if has_link:
            try:
                await message.delete()
                return await message.answer(f"⚠️ {mention}, qrupda link paylaşmaq qadağandır!", parse_mode="Markdown")
            except: pass

    # STİKER VƏ GİF QADAĞASI
    db_cursor.execute("SELECT stiker_bloku FROM settings WHERE chat_id = ?", (c_id,))
    s = db_cursor.fetchone()
    if s and s[0] == 1:
        if message.sticker or message.animation:
            try:
                return await message.delete()
            except: pass

    # SAYĞAC
    if not (message.text and message.text.startswith("/")):
        db_cursor.execute("INSERT OR REPLACE INTO user_info VALUES (?, ?)", (u_id, message.from_user.first_name))
        for k in ["günlük", "həftəlik", "aylıq", "ümumi"]:
            db_cursor.execute("INSERT OR IGNORE INTO scores (chat_id, user_id, kateqoriya) VALUES (?, ?, ?)", (c_id, u_id, k))
            db_cursor.execute("UPDATE scores SET msg_sayi = msg_sayi + 1 WHERE chat_id = ? AND user_id = ? AND kateqoriya = ?", (c_id, u_id, k))
        db_conn.commit()

# ==========================================================
# 9. START
# ==========================================================
async def reset_timer():
    while True:
        now = datetime.now()
        if now.hour == 0 and now.minute == 0:
                        db_cursor.execute("UPDATE scores SET msg_sayi = 0 WHERE kateqoriya = 'günlük'")
            if now.weekday() == 0:
                db_cursor.execute("UPDATE scores SET msg_sayi = 0 WHERE kateqoriya = 'həftəlik'")
            if now.day == 1:
                db_cursor.execute("UPDATE scores SET msg_sayi = 0 WHERE kateqoriya = 'aylıq'")
            db_conn.commit()
            await asyncio.sleep(60)
        await asyncio.sleep(30)

async def main():
    asyncio.create_task(reset_timer())
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
