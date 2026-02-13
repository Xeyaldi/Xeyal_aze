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
    BotCommand,
    ContentType
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

# --- 🛑 BAYAQKI KİMİ SİLƏN HİSSƏ (BUNA TOXUNMA) ---
# Bu handler hər şeyi tutub süzgəcdən keçirir
@dp.message()
async def main_handler(message: Message):
    if not message.chat or message.chat.type not in ["group", "supergroup"]:
        return

    chat_id = message.chat.id
    status = await check_admin_status(chat_id, message.from_user.id)
    
    # 1. STİKER VƏ GİF SİLMƏ (Əsas Problem Burda İdi)
    if message.sticker or message.animation or message.video_note:
        if group_settings.get(chat_id, {}).get("sticker_block") == True:
            if status == "user":
                try:
                    await bot.delete_message(chat_id, message.message_id)
                    return # Silindisə dayansın
                except:
                    pass

    # 2. SÖYÜŞ VƏ LİNK SİLMƏ
    if message.text:
        text_lower = message.text.lower()
        if status == "user":
            if any(w in text_lower for w in BAD_WORDS) or "t.me/" in text_lower or "http" in text_lower:
                try:
                    await message.delete()
                    return
                except:
                    pass
        
        # 3. FİLTERLƏR
        if chat_id in custom_filters:
            for k, v in custom_filters[chat_id].items():
                if k in text_lower:
                    await message.reply(v)
                    return

# --- KOMANDALAR (İXTİSARSIZ) ---

@dp.message(Command("stiker"))
async def cmd_stiker(message: Message, command: CommandObject):
    if await check_admin_status(message.chat.id, message.from_user.id) == "user": return
    if not command.args:
        return await message.answer("İstifadə: /stiker off və ya /stiker on")
    
    choice = command.args.lower()
    if choice == "off":
        group_settings[message.chat.id] = {"sticker_block": True}
        await message.answer("🚫 Stiker və Gif bloku aktiv edildi.")
    elif choice == "on":
        group_settings[message.chat.id] = {"sticker_block": False}
        await message.answer("✅ Stiker bloku deaktiv edildi.")

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("🤖 Flower Premium Botu İşləyir!")

@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer("📜 Əmrlər: /newfed, /admin, /purge, /filter, /stiker off/on, /lock")

@dp.message(Command("admin"))
async def cmd_promote(message: Message, command: CommandObject):
    if await check_admin_status(message.chat.id, message.from_user.id) == "user": return
    if not message.reply_to_message: return
    title = command.args if command.args else "Admin"
    try:
        await bot.promote_chat_member(message.chat.id, message.reply_to_message.from_user.id, can_delete_messages=True)
        await bot.set_chat_administrator_custom_title(message.chat.id, message.reply_to_message.from_user.id, title)
        await message.answer(f"✅ {title} rütbəsi verildi.")
    except: pass

@dp.message(Command("purge"))
async def cmd_purge(message: Message):
    if await check_admin_status(message.chat.id, message.from_user.id) == "user": return
    if not message.reply_to_message: return
    for i in range(message.reply_to_message.message_id, message.message_id + 1):
        try: await bot.delete_message(message.chat.id, i)
        except: continue

@dp.message(Command("newfed"))
async def cmd_newfed(message: Message, command: CommandObject):
    if not command.args: return
    fed_id = str(message.from_user.id)[:5]
    fed_db[fed_id] = {"name": command.args, "owner": message.from_user.id}
    await message.answer(f"✅ Fed yaradıldı. ID: {fed_id}")

# --- 🚀 BOTUN BAŞLADILMASI ---
async def main():
    # Bu hissə botun qrupda hər şeyi görməsini təmin edir (Privacy ayarından asılı olmayaraq)
    await dp.start_polling(bot, allowed_updates=["message", "chat_member", "callback_query"])

if __name__ == '__main__':
    asyncio.run(main())
