import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- KONFİQURASİYA ---
OWNER_ID = 8024893255 
API_TOKEN = os.getenv("BOT_TOKEN") 

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- MƏLUMAT BAZALARI ---
fed_db = {}           
group_feds = {}       
group_settings = {}   
BAD_WORDS = ["söyüş1", "söyüş2", "gic", "fahişə", "qəhbə", "bic", "peysər", "sik", "amcıq"] 

# --- ADMİN YOXLAMA ---
async def is_admin(chat_id, user_id):
    if user_id == OWNER_ID: return True
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ["administrator", "creator"]
    except: return False

# --- ⚙️ KOMANDALAR (Filtrlərdən QABAQ gəlməlidir ki, bot əmrləri silməsin) ---

@dp.message(Command("start"))
async def start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Məni Qrupa Əlavə Et ➕", url=f"https://t.me/{(await bot.get_me()).username}?startgroup=true"))
    await message.answer(f"🤖 **HT-Security Premium Bot** aktivdir!", reply_markup=builder.as_markup())

@dp.message(Command("stiker"))
async def st_toggle(message: types.Message, command: CommandObject):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not command.args: return await message.answer("İstifadə: `/stiker off` və ya `/stiker on` ")
    
    status = (command.args.lower() == "off")
    if message.chat.id not in group_settings: group_settings[message.chat.id] = {}
    group_settings[message.chat.id]["sticker_block"] = status
    await message.answer(f"🚫 Stiker bloku: {'**Aktiv**' if status else '**Deaktiv**'}")

@dp.message(Command("admin"))
async def promote_admin(message: types.Message, command: CommandObject):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return await message.answer("Reply edin.")
    title = command.args or "Admin"
    try:
        await bot.promote_chat_member(message.chat.id, message.reply_to_message.from_user.id, can_delete_messages=True, can_restrict_members=True)
        await bot.set_chat_administrator_custom_title(message.chat.id, message.reply_to_message.from_user.id, title)
        await message.answer(f"✅ {message.reply_to_message.from_user.first_name} indi **{title}**!")
    except: pass

@dp.message(Command("purge"))
async def purge_msgs(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    for i in range(message.reply_to_message.message_id, message.message_id + 1):
        try: await bot.delete_message(message.chat.id, i)
        except: continue

# --- 🛑 SƏNİN QƏTİ SİLMƏ MƏNTİQİN (Əmrlərdən sonra gəlir ki, bot çaşmasın) ---

@dp.message()
async def global_filter(message: types.Message):
    if not message.chat or message.chat.type == "private": return
    chat_id = message.chat.id
    
    # Admin deyilsə yoxla
    if not await is_admin(chat_id, message.from_user.id):
        # 1. Stiker və Gif silmə (Sənin kodun)
        if group_settings.get(chat_id, {}).get("sticker_block", False):
            if message.sticker or message.animation or message.video_note:
                try: return await message.delete()
                except: pass

        # 2. Söyüş silmə (Sənin kodun)
        if message.text:
            if any(word in message.text.lower() for word in BAD_WORDS):
                try: return await message.delete()
                except: pass

# --- BOTUN İŞƏ SALINMASI ---
async def main():
    # allowed_updates mütləqdir
    await dp.start_polling(bot, allowed_updates=["message", "chat_member", "callback_query"])

if __name__ == '__main__':
    asyncio.run(main())
