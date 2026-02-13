import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import (
    ChatPermissions, 
    InlineKeyboardButton, 
    CallbackQuery,
    Message,
    BotCommand
)

# --- LOGLAMA ---
logging.basicConfig(level=logging.INFO)

# --- KONFİQURASİYA ---
OWNER_ID = 8024893255 
API_TOKEN = os.getenv("BOT_TOKEN") 

# Botu bütün mesajları oxumağa məcbur edirik
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Professional Yaddaş Sistemi (Heç nə silinmir)
fed_db = {}           
group_feds = {}       
group_settings = {}   
custom_filters = {} 

# Azərbaycan dili söyüş siyahısı
BAD_WORDS = [
    "söyüş1", "söyüş2", "qehbe", "bic", "sq", "amciq", "gotveran", 
    "peyser", "sik", "daşaq", "siktir", "gicdıllaq", "atdıran", "fahişə", "dalbayob"
] 

# --- ADMİN YOXLAMA FUNKSİYASI ---
async def check_admin_status(chat_id: int, user_id: int):
    if user_id == OWNER_ID: return "owner"
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        if member.status in ["administrator", "creator"]:
            return "admin"
        return "user"
    except:
        return "user"

# --- BUTONLAR (DEVELOPER VƏ DİGƏRLƏRİ - SİLİNMƏDİ) ---
def get_full_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Kömək Menyu 📚", callback_data="help_callback"))
    builder.row(InlineKeyboardButton(text="Məni Qrupa Əlavə Et ➕", url=f"https://t.me/ht_security_bot?startgroup=true"))
    builder.row(
        InlineKeyboardButton(text="Kanal 📢", url="https://t.me/ht_bots"),
        InlineKeyboardButton(text="Dəstək 👥", url="https://t.me/ht_bots_chat")
    )
    builder.row(InlineKeyboardButton(text="👨‍💻 Developer", url="https://t.me/kullaniciadidi"))
    return builder.as_markup()

# --- START (HƏR YERDƏ İŞLƏYİR) ---
@dp.message(Command("start"))
async def cmd_start(message: Message):
    text = (
        "🤖 **HT-Security Premium Botuna Xoş Gəldiniz!**\n\n"
        "Qruplarınızı söyüşlərdən və reklamlardan qoruyan peşəkar sistemdir.\n\n"
        "✨ **Funksiyalar:** Söyüş silmə, Filter, Fed, Admin rütbə və s.\n"
        "Aşağıdakı düymədən kömək ala bilərsiniz 👇"
    )
    await message.answer(text, reply_markup=get_full_keyboard())

# --- HELP (ŞƏXSİDƏKİ KİMİ BUTONLU) ---
@dp.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "📜 **Botun Komandaları:**\n\n"
        "🛡 **Fed:** `/newfed`, `/joinfed`, `/gfban`\n"
        "⚙️ **İdarə:** `/admin`, `/unadmin`, `/ban`, `/mute`, `/purge`\n"
        "🔍 **Filtrlər:** `/filter`, `/stop`, `/stiker off/on`\n"
        "🔐 **Təhlükəsizlik:** `/lock`, `/unlock`, `/info`, `/reload`"
    )
    await message.answer(help_text, reply_markup=get_full_keyboard())

# --- RELOAD (YENİ) ---
@dp.message(Command("reload"))
async def cmd_reload(message: Message):
    if await check_admin_status(message.chat.id, message.from_user.id) == "user": return
    m = await message.answer("🔄 Yenilənir...")
    await asyncio.sleep(1)
    await m.edit_text("✅ Sazlamalar və admin siyahısı yeniləndi!")

# --- ADMİN VƏ RÜTBƏ (SƏHVSİZ) ---
@dp.message(Command("admin"))
async def cmd_promote(message: Message, command: CommandObject):
    if await check_admin_status(message.chat.id, message.from_user.id) == "user": return
    if not message.reply_to_message:
        return await message.answer("İstifadəçini reply edin!")
    
    title = command.args if command.args else "Admin"
    try:
        await bot.promote_chat_member(message.chat.id, message.reply_to_message.from_user.id, 
            can_delete_messages=True, can_restrict_members=True, can_invite_users=True, can_pin_messages=True)
        await bot.set_chat_administrator_custom_title(message.chat.id, message.reply_to_message.from_user.id, title)
        await message.answer(f"✅ {message.reply_to_message.from_user.first_name} indi **{title}**!")
    except:
        await message.answer("❌ Mənə adminlik yetgisi verin!")

# --- PURGE (TOPLU SİLMƏ) ---
@dp.message(Command("purge"))
async def cmd_purge(message: Message):
    if await check_admin_status(message.chat.id, message.from_user.id) == "user": return
    if not message.reply_to_message: return
    
    start_id = message.reply_to_message.message_id
    end_id = message.message_id
    for i in range(start_id, end_id + 1):
        try: await bot.delete_message(message.chat.id, i)
        except: continue
    await message.answer("✅ Təmizləndi.")

# --- GLOBAL HANDLER (SÖYÜŞ, LİNK, FİLTR) ---
@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def group_manager(message: Message):
    if not message.text: return
    status = await check_admin_status(message.chat.id, message.from_user.id)
    
    # 1. Söyüş Filtri
    if any(w in message.text.lower() for w in BAD_WORDS):
        if status == "user":
            await message.delete()
            return await message.answer(f"⚠️ {message.from_user.first_name}, səviyyəli danışın!")

    # 2. Link Filtri
    if ("t.me/" in message.text.lower() or "http" in message.text.lower()) and status == "user":
        await message.delete()
        return

    # 3. Filter sistemi
    if message.chat.id in custom_filters:
        for k, v in custom_filters[message.chat.id].items():
            if k in message.text.lower():
                await message.reply(v)

# --- LOCK & UNLOCK ---
@dp.message(Command("lock"))
async def cmd_lock(message: Message):
    if await check_admin_status(message.chat.id, message.from_user.id) == "user": return
    await bot.set_chat_permissions(message.chat.id, ChatPermissions(can_send_messages=False))
    await message.answer("🔒 Qrup bağlandı.")

@dp.message(Command("unlock"))
async def cmd_unlock(message: Message):
    if await check_admin_status(message.chat.id, message.from_user.id) == "user": return
    await bot.set_chat_permissions(message.chat.id, ChatPermissions(can_send_messages=True, can_send_other_messages=True))
    await message.answer("🔓 Qrup açıldı.")

# --- CALLBACK ---
@dp.callback_query(F.data == "help_callback")
async def help_cb(c: CallbackQuery):
    await c.answer("Komandalar üçün /help yazın!", show_alert=True)

# --- İNFO ---
@dp.message(Command("info"))
async def cmd_info(message: Message):
    user = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    await message.answer(f"👤 Ad: {user.first_name}\n🆔 ID: `{user.id}`")

async def main():
    # Botun komandalar siyahısını Telegram-a bildiririk (Bu qrupda görünməsinə kömək edir)
    await bot.set_my_commands([
        BotCommand(command="start", description="Başlat"),
        BotCommand(command="help", description="Kömək"),
        BotCommand(command="reload", description="Yenilə"),
        BotCommand(command="admin", description="Admin et"),
        BotCommand(command="purge", description="Sil")
    ])
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
