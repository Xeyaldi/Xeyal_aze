import asyncio
import os
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import (
    ChatPermissions, 
    InlineKeyboardButton, 
    Message,
    BotCommand,
    CallbackQuery
)

# --- LOGLAMA ---
logging.basicConfig(level=logging.INFO)

# --- KONFİQURASİYA ---
OWNER_ID = 8024893255 
API_TOKEN = os.getenv("BOT_TOKEN") 

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- MƏLUMAT BAZALARI (SƏNİN BÜTÜN SİSTEMLƏRİN) ---
fed_db = {}           
group_feds = {}       
group_settings = {}   
custom_filters = {} 
user_warns = {}

# Söyüş siyahısı
BAD_WORDS = ["söyüş1", "söyüş2", "qehbe", "bic", "sq", "amciq", "gotveran", "peyser", "sik", "daşaq", "siktir", "gicdıllaq", "atdıran", "fahişə", "dalbayob"] 

# --- ADMİN YOXLAMA (YALNIZ KOMANDALARI İŞLƏTMƏK ÜÇÜN) ---
async def check_admin_status(chat_id: int, user_id: int):
    if user_id == OWNER_ID: return "owner"
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        if member.status in ["administrator", "creator"]:
            return "admin"
        return "user"
    except:
        return "user"

# --- 🛑 1. QƏTİ SİLMƏ MƏNTİQİ (ADMİN-USER FƏRQİ QOYMADAN) ---
@dp.message(lambda m: m.sticker or m.animation or m.video_note)
async def global_media_cleaner(message: Message):
    if not message.chat or message.chat.type == "private": return
    chat_id = message.chat.id
    
    # Əgər stiker bloku aktivdirsə, HƏR KƏSİN mesajı silinir
    if group_settings.get(chat_id, {}).get("sticker_block") == True:
        try: await message.delete()
        except: pass

# --- ⚙️ 2. BÜTÜN KOMANDALAR (MUTE VAXTI VƏ DİGƏRLƏRİ DƏ DAXİL) ---

@dp.message(Command("start"))
async def cmd_start(message: Message):
    builder = InlineKeyboardBuilder()
    me = await bot.get_me()
    builder.row(InlineKeyboardButton(text="Məni Qrupa Əlavə Et ➕", url=f"https://t.me/{me.username}?startgroup=true"))
    await message.answer("🤖 **HT-Security Premium** aktivdir!\nBütün admin əmrləri və qəti qoruma sistemi işləyir.", reply_markup=builder.as_markup())

@dp.message(Command("stiker"))
async def cmd_stiker(message: Message, command: CommandObject):
    if await check_admin_status(message.chat.id, message.from_user.id) == "user": return
    if not command.args: return await message.answer("İstifadə: `/stiker off` (bloklayır)")
    
    choice = command.args.lower()
    if choice == "off":
        group_settings[message.chat.id] = {"sticker_block": True}
        await message.answer("🚫 **Stiker bloku hamı üçün aktiv edildi!**")
    elif choice == "on":
        group_settings[message.chat.id] = {"sticker_block": False}
        await message.answer("✅ **Stiker bloku açıldı.**")

# --- MUTE (VAXTLI) ---
@dp.message(Command("mute"))
async def cmd_mute(message: Message, command: CommandObject):
    if await check_admin_status(message.chat.id, message.from_user.id) == "user": return
    if not message.reply_to_message: return await message.answer("İstifadəçini reply edin.")
    
    until_date = None
    if command.args: # Məsələn: /mute 10m
        unit = command.args[-1]
        amount = int(command.args[:-1])
        if unit == "m": until_date = datetime.now() + timedelta(minutes=amount)
        elif unit == "h": until_date = datetime.now() + timedelta(hours=amount)
        elif unit == "d": until_date = datetime.now() + timedelta(days=amount)

    try:
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, 
            permissions=ChatPermissions(can_send_messages=False), until_date=until_date)
        await message.answer(f"🤐 {message.reply_to_message.from_user.first_name} {command.args if command.args else 'həmişəlik'} səssizə alındı.")
    except: pass

@dp.message(Command("unmute"))
async def cmd_unmute(message: Message):
    if await check_admin_status(message.chat.id, message.from_user.id) == "user": return
    if not message.reply_to_message: return
    try:
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, 
            permissions=ChatPermissions(can_send_messages=True, can_send_other_messages=True))
        await message.answer(f"🔊 {message.reply_to_message.from_user.first_name} danışa bilər.")
    except: pass

@dp.message(Command("ban"))
async def cmd_ban(message: Message):
    if await check_admin_status(message.chat.id, message.from_user.id) == "user": return
    if not message.reply_to_message: return
    try:
        await bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
        await message.answer(f"✈️ {message.reply_to_message.from_user.first_name} qrupdan qovuldu.")
    except: pass

@dp.message(Command("admin"))
async def cmd_promote(message: Message, command: CommandObject):
    if await check_admin_status(message.chat.id, message.from_user.id) == "user": return
    if not message.reply_to_message: return
    title = command.args if command.args else "Admin"
    try:
        await bot.promote_chat_member(message.chat.id, message.reply_to_message.from_user.id, 
            can_delete_messages=True, can_restrict_members=True, can_invite_users=True, can_pin_messages=True)
        await bot.set_chat_administrator_custom_title(message.chat.id, message.reply_to_message.from_user.id, title)
        await message.answer(f"✅ {message.reply_to_message.from_user.first_name} indi **{title}**!")
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
    await message.answer(f"✅ Fed yaradıldı: {command.args}\nID: `{fed_id}`")

# --- 💬 3. SÖYÜŞ VƏ LİNK SİLMƏ (ADMİN-USER FƏRQİ QOYMADAN) ---
@dp.message(F.text)
async def global_text_manager(message: Message):
    if not message.chat or message.chat.type == "private": return
    text_lower = message.text.lower()

    # Söyüş və ya Link aşkarlandıqda (Hamı üçün silir)
    if any(w in text_lower for w in BAD_WORDS) or "t.me/" in text_lower or "http" in text_lower:
        try: 
            await message.delete()
            return
        except: pass

    # Custom Filter (Reply sistemi)
    if message.chat.id in custom_filters:
        for k, v in custom_filters[message.chat.id].items():
            if k in text_lower: await message.reply(v)

# --- 🚀 4. İŞƏ SALMA ---
async def main():
    await bot.set_my_commands([
        BotCommand(command="start", description="Başlat"),
        BotCommand(command="stiker", description="Stiker bloku"),
        BotCommand(command="mute", description="Səssizə al (m/h/d)"),
        BotCommand(command="purge", description="Təmizlə")
    ])
    await dp.start_polling(bot, allowed_updates=["message", "chat_member", "callback_query"])

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
