import asyncio
import os
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import ChatPermissions, BotCommand, InlineKeyboardButton

# --- LOGLAMA SİSTEMİ ---
logging.basicConfig(level=logging.INFO)

# --- KONFİQURASİYA ---
OWNER_ID = 8024893255 
API_TOKEN = os.getenv("BOT_TOKEN") 

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Professional Məlumat Bazası (RAM)
fed_db = {}           
group_feds = {}       
group_settings = {}   
custom_filters = {} 
antispam_db = {} # {user_id: [last_message_time, count]}

# Azərbaycan dili söyüş siyahısı (Maksimum genişlikdə)
BAD_WORDS = [
    "söyüş1", "söyüş2", "qehbe", "bic", "sq", "amciq", "gotveran", 
    "peyser", "sik", "daşaq", "siktir", "gicdıllaq", "atdıran", "fahişə", "dalbayob"
] 

# --- KÖMƏKÇİ FUNKSİYA: ADMİN YOXLAMA ---
async def check_admin_status(chat_id: int, user_id: int):
    if user_id == OWNER_ID: return "owner"
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        if member.status in ["administrator", "creator"]:
            return "admin"
        return "user"
    except Exception:
        return "user"

# --- START MESAJI (YENİLƏNDİ: BOT HAQQINDA MƏLUMAT + HELP DÜYMƏSİ) ---
@dp.message(Command("start"), F.chat.type == "private")
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    
    # Düymələr
    builder.row(InlineKeyboardButton(text="Kömək Menyu 📚", callback_data="help_callback"))
    builder.row(InlineKeyboardButton(text="Məni Qrupa Əlavə Et ➕", url=f"https://t.me/{(await bot.get_me()).username}?startgroup=true"))
    builder.row(
        InlineKeyboardButton(text="Kanal 📢", url="https://t.me/ht_bots"),
        InlineKeyboardButton(text="Dəstək 👥", url="https://t.me/ht_bots_chat")
    )
    
    bot_info = (
        "🤖 **HT-Security Premium Botuna Xoş Gəldiniz!**\n\n"
        "Mən qruplarınızı söyüşlərdən, reklamlardan və arzuolunmaz şəxslərdən qorumaq üçün yaradılmış "
        "peşəkar idarəetmə botuyam. Rose və GroupHelp funksiyaları ilə tam təchiz olunmuşam.\n\n"
        "✨ **Mənimlə nə edə bilərsiniz?**\n"
        "• Söyüş və Linkləri avtomatik silə bilərəm.\n"
        "• Qrupda xüsusi filtrlər yarada bilərəm.\n"
        "• Federasiya sistemi ilə qlobal qoruma təmin edirəm.\n"
        "• Admin rütbələrini idarə edirəm.\n\n"
        "Aşağıdakı düyməyə basaraq bütün əmrlərimi görə bilərsiniz 👇"
    )
    await message.answer(bot_info, reply_markup=builder.as_markup())

# --- CALLBACK HANDLER (HELP DÜYMƏSİ ÜÇÜN) ---
@dp.callback_query(F.data == "help_callback")
async def help_callback(callback: types.CallbackQuery):
    await callback.message.edit_text("Kömək menyusunu görmək üçün çata /help yazın.")

# --- HELP MESAJI ---
@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        "📜 **Botun Geniş Əmrləri:**\n\n"
        "🛡 **Federasiya:**\n"
        "• `/newfed [ad]` - Yeni Fed yaradır\n"
        "• `/joinfed [ID]` - Qrupu Fed-ə bağlayır\n"
        "• `/gfban` - Fed banı (Reply)\n"
        "• `/ggroupfed` - Qrupun Fed məlumatı\n\n"
        "⚙️ **İdarəetmə:**\n"
        "• `/admin [rütbə]` - Admin rütbəsi verir (Reply)\n"
        "• `/unadmin` - Adminliyi alır\n"
        "• `/ban` / `/unban` - Qovur/Açır\n"
        "• `/mute` / `/unmute` - Səssizə alır\n"
        "• `/purge` - Mesajları toplu silir (Reply-dan aşağı)\n\n"
        "🔍 **Filtrlər:**\n"
        "• `/filter [söz]` - Xüsusi cavab (Reply)\n"
        "• `/stop [söz]` - Filtri silir\n"
        "• `/stiker off/on` - Stikerləri bağlayır\n\n"
        "🔐 **Təhlükəsizlik:**\n"
        "• `/lock` / `/unlock` - Qrupu bağla/aç\n"
        "• `/info` - İstifadəçi ID məlumatı"
    )
    await message.answer(help_text)

# --- PURGE (MESAJLARI TOPLU SİLMƏ - YENİ) ---
@dp.message(Command("purge"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_purge(message: types.Message):
    if await check_admin_status(message.chat.id, message.from_user.id) == "user": return
    if not message.reply_to_message:
        return await message.answer("Silmək üçün bir mesajı reply edin.")
    
    msg_id = message.reply_to_message.message_id
    curr_id = message.message_id
    
    for i in range(msg_id, curr_id + 1):
        try:
            await bot.delete_message(message.chat.id, i)
        except: continue
    await message.answer("✅ Mesajlar təmizləndi.")

# --- ADMİN VƏ RÜTBƏ SİSTEMİ ---
@dp.message(Command("admin"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_promote(message: types.Message, command: CommandObject):
    if await check_admin_status(message.chat.id, message.from_user.id) == "user": return
    if not message.reply_to_message: return await message.answer("İstifadəçini reply edin.")
    
    target_id = message.reply_to_message.from_user.id
    if await check_admin_status(message.chat.id, target_id) != "user":
        return await message.answer("❗ Bu istifadəçi artıq admindir.")

    title = command.args if command.args else "Admin"
    try:
        await bot.promote_chat_member(message.chat.id, target_id, can_delete_messages=True, can_restrict_members=True, can_pin_messages=True, can_invite_users=True)
        await bot.set_chat_administrator_custom_title(message.chat.id, target_id, title)
        await message.answer(f"✅ {message.reply_to_message.from_user.first_name} indi **{title}**!")
    except: await message.answer("❌ Yetgi xətası.")

# --- GLOBAL HANDLER (SÖYÜŞ, FİLTR, SPAM) ---
@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def main_handler(message: types.Message):
    if not message.text and not message.sticker: return
    user_status = await check_admin_status(message.chat.id, message.from_user.id)
    chat_id = message.chat.id

    # 1. Söyüş Filtri
    if message.text:
        if any(word in message.text.lower() for word in BAD_WORDS):
            if user_status == "user":
                await message.delete()
                return await message.answer(f"⚠️ {message.from_user.first_name}, xahiş olunur qrupda səviyyəli danışın!")

        # 2. Link Filtri
        if ("t.me/" in message.text.lower() or "http" in message.text.lower()) and user_status == "user":
            await message.delete()
            return

        # 3. Custom Filter
        if chat_id in custom_filters:
            for kw, rep in custom_filters[chat_id].items():
                if kw in message.text.lower():
                    return await message.reply(rep)

    # 4. Stiker Bloku
    if (message.sticker or message.animation) and group_settings.get(chat_id, {}).get("sticker_block"):
        if user_status == "user": await message.delete()

# --- DİGƏR KOMANDALAR (MUTE, LOCK, FED) ---
@dp.message(Command("mute"))
async def cmd_mute(message: types.Message):
    if await check_admin_status(message.chat.id, message.from_user.id) == "user": return
    if not message.reply_to_message: return
    await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, permissions=ChatPermissions(can_send_messages=False))
    await message.answer(f"🔇 {message.reply_to_message.from_user.first_name} sussuruldu.")

@dp.message(Command("lock"))
async def cmd_lock(message: types.Message):
    if await check_admin_status(message.chat.id, message.from_user.id) == "user": return
    await bot.set_chat_permissions(message.chat.id, ChatPermissions(can_send_messages=False))
    await message.answer("🔒 Qrup bağlandı.")

@dp.message(Command("filter"))
async def cmd_filter(message: types.Message, command: CommandObject):
    if await check_admin_status(message.chat.id, message.from_user.id) == "user": return
    if not message.reply_to_message or not command.args: return
    kw = command.args.lower()
    if chat_id not in custom_filters: custom_filters[chat_id] = {}
    custom_filters[message.chat.id][kw] = message.reply_to_message.text
    await message.answer(f"✅ '{kw}' filtri yaradıldı.")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
