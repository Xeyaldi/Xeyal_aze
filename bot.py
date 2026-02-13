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

# --- MƏLUMAT BAZASI (İXTİSARSIZ) ---
fed_db = {}           
group_settings = {}   
custom_filters = {} 

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

# --- STİKER VƏ GİF TUTUCU (ƏN VACİB HİSSƏ) ---
@dp.message(F.sticker | F.animation | F.video_note)
async def handle_media_blocks(message: Message):
    chat_id = message.chat.id
    status = await check_admin_status(chat_id, message.from_user.id)
    
    # Əgər stiker bloku aktivdirsə və yazan admin deyilsə - SİL
    if group_settings.get(chat_id, {}).get("sticker_block") and status == "user":
        try:
            await message.delete()
        except Exception as e:
            logging.error(f"Silmə xətası: {e}")

# --- KOMANDALAR ---

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("🤖 Flower Premium Botuna Xoş Gəldiniz!", reply_markup=get_main_btns())

@dp.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "📜 Botun Əmrləri:\n"
        "🛡 Federasiya: /newfed, /joinfed, /gfban\n"
        "⚙️ İdarəetmə: /admin, /unadmin, /ban, /mute, /purge\n"
        "🔍 Filtrlər: /filter, /stop, /stiker off/on\n"
        "🔐 Təhlükəsizlik: /lock, /unlock, /reload"
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

@dp.message(Command("purge"))
async def cmd_purge(message: Message):
    if await check_admin_status(message.chat.id, message.from_user.id) == "user": return
    if not message.reply_to_message: return
    for i in range(message.reply_to_message.message_id, message.message_id + 1):
        try: await bot.delete_message(message.chat.id, i)
        except: continue
    await message.answer("✅ Təmizləndi.")

# --- GLOBAL HANDLER (SÖYÜŞ VƏ LİNK) ---
@dp.message(F.text)
async def text_handler(message: Message):
    if message.chat.type not in ["group", "supergroup"]: return
    status = await check_admin_status(message.chat.id, message.from_user.id)
    text_lower = message.text.lower()

    if status == "user":
        if any(w in text_lower for w in BAD_WORDS) or "t.me/" in text_lower or "http" in text_lower:
            try: await message.delete()
            except: pass
            return

    # Custom Filter
    if message.chat.id in custom_filters:
        for k, v in custom_filters[message.chat.id].items():
            if k in text_lower: return await message.reply(v)

async def main():
    await bot.set_my_commands([
        BotCommand(command="start", description="Başlat"),
        BotCommand(command="stiker", description="Stiker bloku"),
        BotCommand(command="purge", description="Təmizlə")
    ])
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
