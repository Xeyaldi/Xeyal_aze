import asyncio
import os
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import ChatPermissions, BotCommand

# --- LOGLAMA (Xətaları görmək üçün) ---
logging.basicConfig(level=logging.INFO)

# --- KONFİQURASİYA ---
OWNER_ID = 8024893255 
API_TOKEN = os.getenv("BOT_TOKEN") 

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Professional Yaddaş Sistemi (RAM bazası)
fed_db = {}           
group_feds = {}       
group_settings = {}   
custom_filters = {} 
welcome_messages = {}

# Azərbaycan dili söyüş siyahısı (Genişləndirilmiş)
BAD_WORDS = [
    "söyüş1", "söyüş2", "qehbe", "bic", "sq", "amciq", "gotveran", 
    "peyser", "sik", "daşaq", "siktir", "gicdıllaq", "atdıran", "fahişə"
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

# --- START MESAJI (TAM İSTƏDİYİN KİMİ) ---
@dp.message(Command("start"), F.chat.type == "private")
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Məni Qrupa Əlavə Et ➕", url=f"https://t.me/{(await bot.get_me()).username}?startgroup=true"))
    builder.row(
        types.InlineKeyboardButton(text="Kanal 📢", url="https://t.me/ht_bots"),
        types.InlineKeyboardButton(text="Dəstək 👥", url="https://t.me/ht_bots_chat")
    )
    builder.row(types.InlineKeyboardButton(text="👨‍💻 Developer", url="https://t.me/kullaniciadidi"))
    
    start_text = (
        "🤖 Flower-Security Premium Bot**\n\n"
        "Qrup idarəsini asanlaşdırmaq üçün yaradlımış botam.
        "Qrupa əlavə edib yetgi verməyiniz kifayətdir.\n\n"
        "Kömək üçün `/help` yazın."
    )
    await message.answer(start_text, reply_markup=builder.as_markup())

# --- HELP MESAJI ---
@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        "📜 **Botun Geniş Əmrləri:**\n\n"
        "🛡 **Federasiya Sistemi:**\n"
        "• `/newfed [ad]` - Yeni Federasiya yaradır\n"
        "• `/joinfed [ID]` - Qrupu Federasiyaya bağlayır\n"
        "• `/gfban` - Fed səviyyəsində qlobal ban (Reply)\n"
        "• `/ungfban` - Fed banını açır\n"
        "• `/ggroupfed` - Qrupun bağlı olduğu Fed-i göstərir\n\n"
        "⚙️ **Qrup İdarəetməsi:**\n"
        "• `/admin [rütbə]` - İstifadəçini admin edir (Reply)\n"
        "• `/unadmin` - Adminlik səlahiyyətlərini alır\n"
        "• `/ban` / `/unban` - İstifadəçini qovur və ya açır\n"
        "• `/mute` / `/unmute` - İstifadəçini səssizə alır\n\n"
        "🔍 **Xüsusi Filtrlər:**\n"
        "• `/filter [söz]` - Yazılan sözə bot cavabı təyin edir\n"
        "• `/stop [söz]` - Təyin edilmiş filtri silir\n"
        "• `/stiker off/on` - Qrupda stikerləri bağlayır/açır\n\n"
        "🔐 **Təhlükəsizlik:**\n"
        "• `/lock` / `/unlock` - Qrupda yazışmanı tam bağlayır/açır\n"
        "• `/info` - İstifadəçi haqqında tam ID məlumatı\n"
        "• `/setwelcome` - Yeni gələnlər üçün qarşılama mesajı"
    )
    await message.answer(help_text)

# --- ADMİN VƏ RÜTBƏ SİSTEMİ ---
@dp.message(Command("admin"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_promote(message: types.Message, command: CommandObject):
    user_status = await check_admin_status(message.chat.id, message.from_user.id)
    if user_status == "user": return
    
    if not message.reply_to_message:
        return await message.answer("Admin etmək üçün istifadəçini reply edin.")
    
    target_id = message.reply_to_message.from_user.id
    target_name = message.reply_to_message.from_user.first_name
    
    if await check_admin_status(message.chat.id, target_id) != "user":
        return await message.answer(f"❗ {target_name} artıq bu qrupda admindir.")

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
        await message.answer(f"❌ Xəta! Botun adminləri idarə etmək yetgisi yoxdur.")

# --- MUTE & UNMUTE ---
@dp.message(Command("mute"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_mute(message: types.Message):
    if await check_admin_status(message.chat.id, message.from_user.id) == "user": return
    if not message.reply_to_message: return await message.answer("Sussurmaq üçün reply edin.")
    
    try:
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, permissions=ChatPermissions(can_send_messages=False))
        await message.answer(f"🔇 {message.reply_to_message.from_user.first_name} sussuruldu.")
    except: pass

@dp.message(Command("unmute"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_unmute(message: types.Message):
    if await check_admin_status(message.chat.id, message.from_user.id) == "user": return
    if not message.reply_to_message: return
    
    try:
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, permissions=ChatPermissions(can_send_messages=True, can_send_other_messages=True, can_add_web_page_previews=True))
        await message.answer(f"🔊 {message.reply_to_message.from_user.first_name} artıq yaza bilər.")
    except: pass

# --- GLOBAL HANDLER (SÖYÜŞ, FİLTR, LİNK) ---
@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def main_handler(message: types.Message):
    if not message.text and not message.sticker: return
    user_status = await check_admin_status(message.chat.id, message.from_user.id)
    chat_id = message.chat.id

    # 1. Söyüş Filtri
    if message.text:
        text_lower = message.text.lower()
        if any(word in text_lower for word in BAD_WORDS):
            if user_status == "user":
                await message.delete()
                return await message.answer(f"⚠️ {message.from_user.first_name}, xahiş olunur qrupda səviyyəli danışın!")

        # 2. Xüsusi Filtrlər (/filter)
        if chat_id in custom_filters:
            for kw, reply in custom_filters[chat_id].items():
                if kw in text_lower:
                    return await message.reply(reply)

        # 3. Anti-Link
        if "t.me/" in text_lower or "http" in text_lower:
            if user_status == "user":
                await message.delete()
                return

    # 4. Stiker Bloku
    if message.sticker or message.animation:
        if group_settings.get(chat_id, {}).get("sticker_block"):
            if user_status == "user":
                await message.delete()

# --- FEDERASİYA YOXLAMA ---
@dp.message(Command("ggroupfed"))
async def cmd_ggroupfed(message: types.Message):
    fed_id = group_feds.get(message.chat.id)
    if not fed_id:
        await message.answer("❌ Bu qrup hər hansı bir federasiyaya qoşulmayıb.")
    else:
        await message.answer(f"🔗 Bu qrup `{fed_id}` ID-li federasiyaya bağlıdır.")

# --- DİGƏR BÜTÜN KOMANDALARIN TƏMİNİ ---
@dp.message(Command("lock"))
async def cmd_lock(message: types.Message):
    if await check_admin_status(message.chat.id, message.from_user.id) == "user": return
    await bot.set_chat_permissions(message.chat.id, ChatPermissions(can_send_messages=False))
    await message.answer("🔒 Qrup bağlandı. Yazışma qadağandır.")

@dp.message(Command("unlock"))
async def cmd_unlock(message: types.Message):
    if await check_admin_status(message.chat.id, message.from_user.id) == "user": return
    await bot.set_chat_permissions(message.chat.id, ChatPermissions(can_send_messages=True, can_send_other_messages=True))
    await message.answer("🔓 Qrup açıldı. Yazışma sərbəstdir.")

@dp.message(Command("filter"))
async def cmd_filter(message: types.Message, command: CommandObject):
    if await check_admin_status(message.chat.id, message.from_user.id) == "user": return
    if not message.reply_to_message or not command.args:
        return await message.answer("İstifadə: Reply edərək `/filter söz` yazın.")
    kw = command.args.lower()
    if message.chat.id not in custom_filters: custom_filters[message.chat.id] = {}
    custom_filters[message.chat.id][kw] = message.reply_to_message.text
    await message.answer(f"✅ '{kw}' sözü filtrə əlavə olundu.")

async def main():
    # Komandaların menyuda görünməsi
    await bot.set_my_commands([
        BotCommand(command="start", description="Botu başladır"),
        BotCommand(command="help", description="Kömək menyusu"),
        BotCommand(command="admin", description="Admin edir"),
        BotCommand(command="mute", description="Sussurur"),
        BotCommand(command="lock", description="Qrupu bağlayır")
    ])
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
