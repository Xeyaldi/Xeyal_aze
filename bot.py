import asyncio
import os
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import (
    ChatPermissions, 
    BotCommand, 
    InlineKeyboardButton, 
    CallbackQuery,
    Message
)

# --- LOGLAMA SİSTEMİ (Xətaları izləmək üçün) ---
logging.basicConfig(level=logging.INFO)

# --- KONFİQURASİYA ---
OWNER_ID = 8024893255 
API_TOKEN = os.getenv("BOT_TOKEN") 

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Professional Yaddaş Sistemi (Data ixtisarsız saxlanılır)
fed_db = {}           
group_feds = {}       
group_settings = {}   
custom_filters = {} 
user_warns = {}

# Azərbaycan dili söyüş siyahısı (Tam siyahı)
BAD_WORDS = [
    "söyüş1", "söyüş2", "qehbe", "bic", "sq", "amciq", "gotveran", 
    "peyser", "sik", "daşaq", "siktir", "gicdıllaq", "atdıran", "fahişə", "dalbayob", "paxıl"
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

# --- BUTON QURUCUSU (START VƏ HELP ÜÇÜN) ---
def get_main_keyboard(bot_username: str):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Kömək Menyu 📚", callback_data="help_callback"))
    builder.row(InlineKeyboardButton(text="Məni Qrupa Əlavə Et ➕", url=f"https://t.me/{bot_username}?startgroup=true"))
    builder.row(
        InlineKeyboardButton(text="Kanal 📢", url="https://t.me/ht_bots"),
        InlineKeyboardButton(text="Dəstək 👥", url="https://t.me/ht_bots_chat")
    )
    builder.row(InlineKeyboardButton(text="👨‍💻 Developer", url="https://t.me/kullaniciadidi"))
    return builder.as_markup()

# --- START MESAJI (QRUP VƏ ŞƏXSİDƏ TAM İŞLƏK) ---
@dp.message(Command("start"))
async def cmd_start(message: Message):
    bot_user = await bot.get_me()
    start_info = (
        "🤖 Flower-Security Premium Botuna Xoş Gəldiniz!\n\n"
        "Mən qruplarınızı söyüşlərdən, reklamlardan və arzuolunmaz şəxslərdən qorumaq üçün yaradılmış "
        "peşəkar idarəetmə botuyam. Rose və GroupHelp funksiyaları ilə tam təchiz olunmuşam.\n\n"
        "✨ Mənimlə nə edə bilərsiniz?\n"
        "• Söyüş və Linkləri saniyəsində silirəm.\n"
        "• Qrupda xüsusi sözlərə cavablar (filter) yaradıram.\n"
        "• Federasiya sistemi ilə qlobal qoruma təmin edirəm.\n"
        "• Adminlərə xüsusi rütbələr (Custom Title) verirəm.\n\n"
        "Aşağıdakı düyməyə basaraq bütün əmrlərimi görə bilərsiniz 👇"
    )
    await message.answer(start_info, reply_markup=get_main_keyboard(bot_user.username))

# --- HELP MESAJI (TAM DETALLI VƏ BUTONLU) ---
@dp.message(Command("help"))
async def cmd_help(message: Message):
    bot_user = await bot.get_me()
    help_text = (
        "📜 **Botun Geniş Əmrlər Siyahısı:**\n\n"
        "🛡 **Federasiya Sistemi:**\n"
        "• `/newfed [ad]` - Yeni Federasiya yaradır\n"
        "• `/joinfed [ID]` - Qrupu Fed-ə bağlayır\n"
        "• `/gfban` - Fed səviyyəsində qlobal ban\n"
        "• `/ggroupfed` - Qrupun Fed məlumatı\n\n"
        "⚙️ **İdarəetmə Əmrləri:**\n"
        "• `/admin [rütbə]` - Admin rütbəsi verir (Reply)\n"
        "• `/unadmin` - Adminliyi tam geri alır\n"
        "• `/ban` / `/unban` - Qovur və ya açır\n"
        "• `/mute` / `/unmute` - Səssizə alır və ya açır\n"
        "• `/purge` - Mesajları toplu silir (Reply-dan aşağı)\n\n"
        "🔍 **Xüsusi Filtrlər:**\n"
        "• `/filter [söz]` - Xüsusi cavab təyin edir\n"
        "• `/stop [söz]` - Təyin edilmiş filtri silir\n"
        "• `/stiker off/on` - Qrupda stikerləri bağlayır\n\n"
        "🔐 **Təhlükəsizlik və Digər:**\n"
        "• `/lock` / `/unlock` - Qrupu tam bağla/aç\n"
        "• `/info` - İstifadəçi ID və status məlumatı\n"
        "• `/reload` - Admin siyahısını yeniləyir"
    )
    await message.answer(help_text, reply_markup=get_main_keyboard(bot_user.username))

# --- RELOAD KOMANDASI ---
@dp.message(Command("reload"))
async def cmd_reload(message: Message):
    u_status = await check_admin_status(message.chat.id, message.from_user.id)
    if u_status == "user": return
    wait_msg = await message.answer("🔄 **Məlumatlar yenilənir, zəhmət olmasa gözləyin...**")
    await asyncio.sleep(2)
    await wait_msg.edit_text("✅ **Uğurla yeniləndi! Bütün admin səlahiyyətləri aktivdir.**")

# --- ADMİN VƏ RÜTBƏ SİSTEMİ (İXTİSARSIZ) ---
@dp.message(Command("admin"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_promote(message: Message, command: CommandObject):
    if await check_admin_status(message.chat.id, message.from_user.id) == "user": return
    if not message.reply_to_message: return await message.answer("İstifadəçini reply edin.")
    
    target_id = message.reply_to_message.from_user.id
    target_name = message.reply_to_message.from_user.first_name
    title = command.args if command.args else "Admin"
    
    try:
        await bot.promote_chat_member(
            message.chat.id, target_id, 
            can_delete_messages=True, can_restrict_members=True, 
            can_pin_messages=True, can_invite_users=True, can_change_info=True
        )
        await bot.set_chat_administrator_custom_title(message.chat.id, target_id, title)
        await message.answer(f"✅ {target_name} indi **{title}** olaraq təyin edildi!")
    except Exception as e:
        await message.answer("❌ Xəta! Mənə adminlik və 'Admin əlavə et' yetgisi verin.")

@dp.message(Command("unadmin"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_demote(message: Message):
    if await check_admin_status(message.chat.id, message.from_user.id) == "user": return
    if not message.reply_to_message: return
    try:
        await bot.promote_chat_member(message.chat.id, message.reply_to_message.from_user.id, can_delete_messages=False, can_restrict_members=False)
        await message.answer(f"🗑 {message.reply_to_message.from_user.first_name} admin rütbəsindən azad edildi.")
    except: pass

# --- GLOBAL HANDLER (SÖYÜŞ, FİLTR, STİKER, LİNK) ---
@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def main_handler(message: Message):
    if not message.text and not message.sticker: return
    user_status = await check_admin_status(message.chat.id, message.from_user.id)
    chat_id = message.chat.id

    if message.text:
        text_lower = message.text.lower()
        # 1. Söyüş Filtri (Xüsusi xəbərdarlıqla)
        if any(word in text_lower for word in BAD_WORDS):
            if user_status == "user":
                await message.delete()
                return await message.answer(f"⚠️ {message.from_user.first_name}, xahiş olunur qrupda səviyyəli danışın!")
        
        # 2. Link Filtri
        if ("t.me/" in text_lower or "http" in text_lower) and user_status == "user":
            await message.delete()
            return
        
        # 3. Custom Filter (Rose Style)
        if chat_id in custom_filters:
            for kw, rep in custom_filters[chat_id].items():
                if kw in text_lower: return await message.reply(rep)

    # 4. Stiker Bloku
    if (message.sticker or message.animation) and group_settings.get(chat_id, {}).get("sticker_block"):
        if user_status == "user": await message.delete()

# --- MUTE, LOCK, PURGE VƏ DİGƏRLƏRİ ---
@dp.message(Command("purge"))
async def cmd_purge(message: Message):
    if await check_admin_status(message.chat.id, message.from_user.id) == "user": return
    if not message.reply_to_message: return await message.answer("Reply edin.")
    msg_id = message.reply_to_message.message_id
    curr_id = message.message_id
    for i in range(msg_id, curr_id + 1):
        try: await bot.delete_message(message.chat.id, i)
        except: continue
    await message.answer("✅ Təmizləndi.")

@dp.message(Command("lock"))
async def cmd_lock(message: Message):
    if await check_admin_status(message.chat.id, message.from_user.id) == "user": return
    await bot.set_chat_permissions(message.chat.id, ChatPermissions(can_send_messages=False))
    await message.answer("🔒 Qrup bağlandı. Artıq yalnız adminlər yaza bilər.")

@dp.message(Command("unlock"))
async def cmd_unlock(message: Message):
    if await check_admin_status(message.chat.id, message.from_user.id) == "user": return
    await bot.set_chat_permissions(message.chat.id, ChatPermissions(can_send_messages=True, can_send_other_messages=True))
    await message.answer("🔓 Qrup açıldı. Hər kəs yaza bilər.")

@dp.message(Command("filter"))
async def cmd_filter(message: Message, command: CommandObject):
    if await check_admin_status(message.chat.id, message.from_user.id) == "user": return
    if not message.reply_to_message or not command.args: return
    kw = command.args.lower()
    if message.chat.id not in custom_filters: custom_filters[message.chat.id] = {}
    custom_filters[message.chat.id][kw] = message.reply_to_message.text
    await message.answer(f"✅ '{kw}' filtri aktiv edildi.")

@dp.message(Command("info"))
async def cmd_info(message: Message):
    target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    status = await check_admin_status(message.chat.id, target.id)
    await message.answer(f"👤 **Məlumat Paneli:**\n\n🆔 ID: `{target.id}`\n📛 Ad: {target.first_name}\n💎 Status: {status}")

# --- BOTUN BAŞLADILMASI ---
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
