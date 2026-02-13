import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import (
    ChatPermissions, 
    InlineKeyboardButton, 
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

# --- MƏLUMAT BAZALARI (SIFIR İXTİSAR) ---
fed_db = {}           
group_feds = {}       
group_settings = {}   
custom_filters = {} 
user_warns = {}

# Söyüş siyahısı
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

# --- BUTONLAR ---
def get_main_btns():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Kömək Menyu 📚", callback_data="help_callback"))
    builder.row(InlineKeyboardButton(text="Məni Qrupa Əlavə Et ➕", url=f"https://t.me/Miss_Flower_bot?startgroup=true"))
    builder.row(
        InlineKeyboardButton(text="Kanal 📢", url="https://t.me/ht_bots"),
        InlineKeyboardButton(text="Dəstək 👥", url="https://t.me/ht_bots_chat")
    )
    builder.row(InlineKeyboardButton(text="👨‍💻 Developer", url="https://t.me/kullaniciadidi"))
    return builder.as_markup()

# --- 1. MEDIA TUTUCU (HƏR ŞEYDƏN ƏVVƏL BU İŞLƏYİR) ---
@dp.message(F.sticker | F.animation | F.video_note)
async def media_blocker(message: Message):
    chat_id = message.chat.id
    status = await check_admin_status(chat_id, message.from_user.id)
    
    # Əgər stiker bloku aktivdirsə və yazan admin deyilsə - DƏRHAL SİL
    if group_settings.get(chat_id, {}).get("sticker_block") == True and status == "user":
        try:
            await message.delete()
        except:
            pass

# --- 2. KOMANDALAR (TAM VERSİYA) ---

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("🤖 Flower Premium Botuna Xoş Gəldiniz!\n\nMən qruplarınızı qorumaq üçün buradayam.", reply_markup=get_main_btns())

@dp.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "📜 Botun Geniş Əmrləri:\n\n"
        "🛡 Federasiya:\n"
        "• /newfed [ad] - Yeni Fed yaradır\n"
        "• /joinfed [ID] - Qrupu Fed-ə bağlayır\n"
        "• /gfban - Fed banı\n"
        "• /ggroupfed - Fed məlumatı\n\n"
        "⚙️ İdarəetmə:\n"
        "• /admin [rütbə] - Admin et (Reply)\n"
        "• /unadmin - Adminliyi al\n"
        "• /ban - Qov\n"
        "• /mute - Səssizə al\n"
        "• /purge - Təmizlə\n\n"
        "🔍 Filtrlər:\n"
        "• /filter [söz] - Xüsusi cavab\n"
        "• /stop [söz] - Filtri sil\n"
        "• /stiker off - Stikerləri bağla\n"
        "• /stiker on - Stikerləri aç\n\n"
        "🔐 Təhlükəsizlik:\n"
        "• /lock - Qrupu bağla\n"
        "• /unlock - Qrupu aç\n"
        "• /info - ID məlumatı\n"
        "• /reload - Yenilə"
    )
    await message.answer(help_text, reply_markup=get_main_btns())

@dp.message(Command("stiker"))
async def cmd_stiker(message: Message, command: CommandObject):
    if await check_admin_status(message.chat.id, message.from_user.id) == "user": return
    if not command.args: return
    choice = command.args.lower()
    if choice == "off":
        group_settings[message.chat.id] = {"sticker_block": True}
        await message.answer("🚫 Stiker və Gif bloku aktiv edildi. Artıq silinəcəklər.")
    elif choice == "on":
        group_settings[message.chat.id] = {"sticker_block": False}
        await message.answer("✅ Stiker bloku deaktiv edildi.")

@dp.message(Command("reload"))
async def cmd_reload(message: Message):
    if await check_admin_status(message.chat.id, message.from_user.id) == "user": return
    await message.answer("✅ Sazlamalar uğurla yeniləndi!")

@dp.message(Command("admin"))
async def cmd_promote(message: Message, command: CommandObject):
    if await check_admin_status(message.chat.id, message.from_user.id) == "user": return
    if not message.reply_to_message: return await message.answer("İstifadəçini reply edin!")
    title = command.args if command.args else "Admin"
    try:
        await bot.promote_chat_member(message.chat.id, message.reply_to_message.from_user.id, can_delete_messages=True, can_restrict_members=True)
        await bot.set_chat_administrator_custom_title(message.chat.id, message.reply_to_message.from_user.id, title)
        await message.answer(f"✅ {message.reply_to_message.from_user.first_name} indi {title}!")
    except: await message.answer("❌ Xəta!")

@dp.message(Command("purge"))
async def cmd_purge(message: Message):
    if await check_admin_status(message.chat.id, message.from_user.id) == "user": return
    if not message.reply_to_message: return
    for i in range(message.reply_to_message.message_id, message.message_id + 1):
        try: await bot.delete_message(message.chat.id, i)
        except: continue
    await message.answer("✅ Təmizləndi.")

@dp.message(Command("newfed"))
async def cmd_newfed(message: Message, command: CommandObject):
    if not command.args: return
    fed_id = str(message.from_user.id)[:5]
    fed_db[fed_id] = {"name": command.args, "owner": message.from_user.id}
    await message.answer(f"✅ Fed yaradıldı: {command.args}\nID: {fed_id}")

# --- 3. MƏTN TUTUCU (SÖYÜŞ VƏ LİNK) ---
@dp.message(F.text)
async def text_handler(message: Message):
    if message.chat.type not in ["group", "supergroup"]: return
    status = await check_admin_status(message.chat.id, message.from_user.id)
    text_lower = message.text.lower()

    if status == "user":
        # Söyüş və Link
        if any(w in text_lower for w in BAD_WORDS) or "t.me/" in text_lower or "http" in text_lower:
            try: await message.delete()
            except: pass
            return

    # Filter
    if message.chat.id in custom_filters:
        for k, v in custom_filters[message.chat.id].items():
            if k in text_lower: return await message.reply(v)

async def main():
    await bot.set_my_commands([
        BotCommand(command="start", description="Başlat"),
        BotCommand(command="stiker", description="Stiker bloku"),
        BotCommand(command="reload", description="Yenilə")
    ])
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
