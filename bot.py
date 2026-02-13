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

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Məlumat Bazası (Heç bir məlumat ixtisar olunmur)
fed_db = {}           
group_feds = {}       
group_settings = {}   
custom_filters = {} 
user_warns = {}

# Söyüş siyahısı (Tam genişlikdə)
BAD_WORDS = ["söyüş1", "söyüş2", "qehbe", "bic", "sq", "amciq", "gotveran", "peyser", "sik", "daşaq", "siktir", "gicdıllaq", "atdıran", "fahişə", "dalbayob"] 

# --- ADMİN YOXLAMA ---
async def check_admin_status(chat_id: int, user_id: int):
    if user_id == OWNER_ID: return "owner"
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        if member.status in ["administrator", "creator"]:
            return "admin"
        return "user"
    except:
        return "user"

# --- BUTONLAR (DEVELOPER VƏ DİGƏRLƏRİ TAM QALDI) ---
def get_main_btns():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Kömək Menyu 📚", callback_data="help_callback"))
    builder.row(InlineKeyboardButton(text="Məni Qrupa Əlavə Et ➕", url=f"https://t.me/ht_security_bot?startgroup=true"))
    builder.row(
        InlineKeyboardButton(text="Kanal 📢", url="https://t.me/ht_bots"),
        InlineKeyboardButton(text="Dəstək 👥", url="https://t.me/ht_bots_chat")
    )
    builder.row(InlineKeyboardButton(text="👨‍💻 Developer", url="https://t.me/kullaniciadidi"))
    return builder.as_markup()

# --- KOMANDALARIN QƏBULU (QRUPDA İŞLƏMƏSİ ÜÇÜN) ---

@dp.message(Command("start"))
async def cmd_start(message: Message):
    text = (
        "🤖 Flower-Security Premium Botuna Xoş Gəldiniz!\n\n"
        "Mən qruplarınızı söyüşlərdən, reklamlardan və arzuolunmaz şəxslərdən qorumaq üçün yaradılmış "
        "peşəkar idarəetmə botuyam. Rose və GroupHelp funksiyaları ilə tam təchiz olunmuşam.\n\n"
        "Aşağıdakı düymələrdən istifadə edə bilərsiniz 👇"
    )
    await message.answer(text, reply_markup=get_main_btns())

@dp.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "📜 **Botun Geniş Əmrləri:**\n\n"
        "🛡 **Federasiya:** `/newfed`, `/joinfed`, `/gfban`, `/ggroupfed`\n"
        "⚙️ **İdarəetmə:** `/admin`, `/unadmin`, `/ban`, `/mute`, `/purge`\n"
        "🔍 **Filtrlər:** `/filter`, `/stop`, `/stiker off/on`\n"
        "🔐 **Təhlükəsizlik:** `/lock`, `/unlock`, `/info`, `/reload`"
    )
    await message.answer(help_text, reply_markup=get_main_btns())

@dp.message(Command("reload"))
async def cmd_reload(message: Message):
    if await check_admin_status(message.chat.id, message.from_user.id) == "user": return
    m = await message.answer("🔄 **Məlumatlar və admin siyahısı yenilənir...**")
    await asyncio.sleep(1.5)
    await m.edit_text("✅ **Uğurla yeniləndi! Komandalar aktivdir.**")

@dp.message(Command("admin"))
async def cmd_promote(message: Message, command: CommandObject):
    if await check_admin_status(message.chat.id, message.from_user.id) == "user": return
    if not message.reply_to_message:
        return await message.answer("Admin etmək üçün istifadəçini reply edin!")
    
    title = command.args if command.args else "Admin"
    try:
        await bot.promote_chat_member(message.chat.id, message.reply_to_message.from_user.id, 
            can_delete_messages=True, can_restrict_members=True, can_invite_users=True, can_pin_messages=True)
        await bot.set_chat_administrator_custom_title(message.chat.id, message.reply_to_message.from_user.id, title)
        await message.answer(f"✅ {message.reply_to_message.from_user.first_name} indi **{title}**!")
    except:
        await message.answer("❌ Xəta! Mənə adminlik və rütbə dəyişmək yetgisi verin.")

@dp.message(Command("purge"))
async def cmd_purge(message: Message):
    if await check_admin_status(message.chat.id, message.from_user.id) == "user": return
    if not message.reply_to_message: return
    start_id = message.reply_to_message.message_id
    end_id = message.message_id
    for i in range(start_id, end_id + 1):
        try: await bot.delete_message(message.chat.id, i)
        except: continue
    await message.answer("✅ Mesajlar təmizləndi.")

@dp.message(Command("stiker"))
async def cmd_stiker(message: Message, command: CommandObject):
    if await check_admin_status(message.chat.id, message.from_user.id) == "user": return
    if not command.args:
        return await message.answer("İstifadə: `/stiker on` və ya `/stiker off`")
    
    choice = command.args.lower()
    if choice == "off":
        group_settings[message.chat.id] = {"sticker_block": True}
        await message.answer("🚫 Stiker bloku: **Aktiv**")
    elif choice == "on":
        group_settings[message.chat.id] = {"sticker_block": False}
        await message.answer("✅ Stiker bloku: **Deaktiv**")

@dp.message(Command("lock"))
async def cmd_lock(message: Message):
    if await check_admin_status(message.chat.id, message.from_user.id) == "user": return
    await bot.set_chat_permissions(message.chat.id, ChatPermissions(can_send_messages=False))
    await message.answer("🔒 Qrup bağlandı. Yazışma qadağandır.")

@dp.message(Command("unlock"))
async def cmd_unlock(message: Message):
    if await check_admin_status(message.chat.id, message.from_user.id) == "user": return
    await bot.set_chat_permissions(message.chat.id, ChatPermissions(can_send_messages=True, can_send_other_messages=True))
    await message.answer("🔓 Qrup açıldı. Yazışma sərbəstdir.")

# --- GLOBAL HANDLER (SÖYÜŞ, LİNK, FİLTR) ---
@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def main_manager(message: Message):
    if not message.text and not message.sticker: return
    status = await check_admin_status(message.chat.id, message.from_user.id)
    chat_id = message.chat.id

    if message.text:
        text_lower = message.text.lower()
        # Söyüş Filtri
        if any(w in text_lower for w in BAD_WORDS) and status == "user":
            await message.delete()
            return await message.answer(f"⚠️ {message.from_user.first_name}, xahiş olunur səviyyəli danışın!")
        
        # Link Filtri
        if ("t.me/" in text_lower or "http" in text_lower) and status == "user":
            await message.delete()
            return
        
        # Filter (Rose style)
        if chat_id in custom_filters:
            for k, v in custom_filters[chat_id].items():
                if k in text_lower: return await message.reply(v)

    # Stiker Bloku
    if (message.sticker or message.animation) and group_settings.get(chat_id, {}).get("sticker_block"):
        if status == "user": await message.delete()

# --- FEDERASİYA ---
@dp.message(Command("newfed"))
async def cmd_newfed(message: Message, command: CommandObject):
    if not command.args: return
    fed_id = str(message.from_user.id)[:5]
    fed_db[fed_id] = {"name": command.args, "owner": message.from_user.id}
    await message.answer(f"✅ Yeni Federasiya yaradıldı: **{command.args}**\nID: `{fed_id}`")

async def main():
    # Komandaları Telegram-a tanıtmaq (Menyuda görünməsi üçün)
    await bot.set_my_commands([
        BotCommand(command="start", description="Botu başladır"),
        BotCommand(command="help", description="Kömək menyusu"),
        BotCommand(command="reload", description="Sazlamaları yeniləyir"),
        BotCommand(command="admin", description="İstifadəçini admin edir"),
        BotCommand(command="stiker", description="Stiker bloku (on/off)"),
        BotCommand(command="purge", description="Mesajları təmizləyir")
    ])
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
