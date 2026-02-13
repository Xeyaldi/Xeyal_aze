import asyncio
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import ChatPermissions

# --- KONFİQURASİYA ---
OWNER_ID = 8024893255 
API_TOKEN = os.getenv("BOT_TOKEN") 

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Professional Yaddaş
fed_db = {}           
group_feds = {}       
group_settings = {}   
custom_filters = {} 
user_spam_count = {} # Anti-Spam üçün

# Genişləndirilmiş Söyüş Siyahısı
BAD_WORDS = ["söyüş1", "söyüş2", "qehbe", "bic", "sq", "amciq", "gotveran", "peyser", "sik", "daşaq", "siktir", "gicdıllaq"] 

# --- KÖMƏKÇİ FUNKSİYALAR ---
async def check_admin_status(chat_id: int, user_id: int):
    if user_id == OWNER_ID: return "owner"
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        if member.status in ["administrator", "creator"]:
            return "admin"
        return "user"
    except: return "user"

# --- ŞƏXSİ MESAJ QADAĞASI ---
GROUP_ONLY = ["ban", "unban", "mute", "unmute", "admin", "unadmin", "stiker", "ggroupfed", "gfban", "filter", "stop", "info", "lock", "unlock"]
@dp.message(F.chat.type == "private", Command(*GROUP_ONLY))
async def private_restrict(message: types.Message):
    await message.answer("⚠️ Bu əmr yalnız qruplarda istifadə edilə bilər!")

# --- START & HELP (TƏMİZ VƏ SƏLİQƏLİ) ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Məni Qrupa Əlavə Et ➕", url=f"https://t.me/{(await bot.get_me()).username}?startgroup=true"))
    builder.row(types.InlineKeyboardButton(text="👨‍💻 Developer", url="https://t.me/kullaniciadidi"))
    
    text = (
        "🤖 Flower -Security Premium Bot\n\n"
        "Qrupları qorumaq və nizam-intizam yaratmaq üçün yaradılmış peşəkar köməkçiyəm.\n\n"
        "Kömək üçün /help yazın."
    )
    await message.answer(text, reply_markup=builder.as_markup())

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        "📜 **Əmrlər Siyahısı:**\n\n"
        "🛡 **İdarə:** /ban, /unban, /mute, /unmute\n"
        "⚙️ **Admin:** /admin [rütbə], /unadmin\n"
        "🔍 **Filtr:** /filter [söz] (reply), /stop [söz]\n"
        "🔐 **Qoru:** /lock (mesajları bağlayır), /unlock\n"
        "ℹ️ **Məlumat:** /info (reply)\n"
        "🚫 **Tənzimləmə:** /stiker off/on"
    )
    await message.answer(help_text)

# --- LOCK/UNLOCK SİSTEMİ (YENİ) ---
@dp.message(Command("lock"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_lock(message: types.Message):
    if await check_admin_status(message.chat.id, message.from_user.id) == "user": return
    await bot.set_chat_permissions(message.chat.id, ChatPermissions(can_send_messages=False))
    await message.answer("🔒 Qrup bağlandı. Artıq yalnız adminlər yaza bilər.")

@dp.message(Command("unlock"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_unlock(message: types.Message):
    if await check_admin_status(message.chat.id, message.from_user.id) == "user": return
    await bot.set_chat_permissions(message.chat.id, ChatPermissions(can_send_messages=True, can_send_other_messages=True, can_add_web_page_previews=True))
    await message.answer("🔓 Qrup açıldı. Hər kəs yaza bilər.")

# --- İNFO SİSTEMİ (YENİ) ---
@dp.message(Command("info"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_info(message: types.Message):
    target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    status = await check_admin_status(message.chat.id, target.id)
    info_text = (
        f"👤 **İstifadəçi Məlumatı:**\n\n"
        f"🆔 ID: `{target.id}`\n"
        f"📛 Ad: {target.first_name}\n"
        f"💎 Status: {status.capitalize()}\n"
        f"🔗 Username: @{target.username if target.username else 'Yoxdur'}"
    )
    await message.answer(info_text)

# --- FİLTR SİSTEMİ ---
@dp.message(Command("filter"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_filter(message: types.Message, command: CommandObject):
    if await check_admin_status(message.chat.id, message.from_user.id) == "user": return
    if not message.reply_to_message or not command.args:
        return await message.answer("İstifadə: Reply edərək `/filter söz` yazın.")
    keyword = command.args.lower()
    if message.chat.id not in custom_filters: custom_filters[message.chat.id] = {}
    custom_filters[message.chat.id][keyword] = message.reply_to_message.text
    await message.answer(f"✅ '{keyword}' filtri aktiv edildi.")

# --- GLOBAL HANDLER (SÖYÜŞ VƏ SPAM) ---
@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def global_handler(message: types.Message):
    if not message.text: return
    user_status = await check_admin_status(message.chat.id, message.from_user.id)
    text = message.text.lower()

    # 1. Söyüş Filtri (İstədiyin Mesajla)
    if any(word in text for word in BAD_WORDS):
        if user_status == "user":
            await message.delete()
            return await message.answer(f"⚠️ {message.from_user.first_name}, xahiş olunur qrupda səviyyəli danışın!")

    # 2. Custom Filter
    if message.chat.id in custom_filters:
        for key, val in custom_filters[message.chat.id].items():
            if key in text:
                return await message.reply(val)

    # 3. Anti-Link
    if "t.me/" in text or "http" in text:
        if user_status == "user":
            await message.delete()

# --- ADMİN/BAN/MUTE (STABİL) ---
@dp.message(Command("admin"))
async def cmd_admin(message: types.Message, command: CommandObject):
    if await check_admin_status(message.chat.id, message.from_user.id) == "user": return
    if not message.reply_to_message: return
    title = command.args if command.args else "Admin"
    try:
        await bot.promote_chat_member(message.chat.id, message.reply_to_message.from_user.id, can_delete_messages=True, can_restrict_members=True)
        await bot.set_chat_administrator_custom_title(message.chat.id, message.reply_to_message.from_user.id, title)
        await message.answer(f"✅ {message.reply_to_message.from_user.first_name} indi {title}!")
    except: await message.answer("Məni admin edin.")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
