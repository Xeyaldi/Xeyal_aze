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

# --- MƏLUMAT BAZALARI (SIFIR İXTİSAR) ---
fed_db = {}           
group_feds = {}       
group_settings = {}   
custom_filters = {} 
user_warns = {}

# Söyüş siyahısı
BAD_WORDS = ["söyüş1", "söyüş2", "gic", "fahişə", "qəhbə", "bic", "peysər", "sik", "amcıq"] 

# --- ADMİN YOXLAMA FUNKSİYASI ---
async def is_admin(chat_id, user_id):
    if user_id == OWNER_ID: return True
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ["administrator", "creator"]
    except: return False

# --- 🛑 QƏTİ SİLƏN MƏNTİQ (TOXUNULMAZ) ---
@dp.message(lambda m: not m.text or any(x in (m.text or "").lower() for x in BAD_WORDS) or m.sticker or m.animation)
async def global_filter(message: types.Message):
    chat_id = message.chat.id
    if message.chat.type == "private": return
    
    # Əgər admin deyilsə yoxla
    if not await is_admin(chat_id, message.from_user.id):
        # 1. Stiker və Gif bloku
        if group_settings.get(chat_id, {}).get("sticker_block", False):
            if message.sticker or message.animation or message.video_note:
                try: return await message.delete()
                except: pass

        # 2. Söyüş bloku
        if message.text:
            if any(word in message.text.lower() for word in BAD_WORDS):
                try: return await message.delete()
                except: pass

# --- ⚙️ BÜTÜN KOMANDALAR (TAM VƏ DÜZƏLDİLMİŞ) ---

@dp.message(Command("start"))
async def start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Məni Qrupa Əlavə Et ➕", url=f"https://t.me/{(await bot.get_me()).username}?startgroup=true"))
    builder.row(
        types.InlineKeyboardButton(text="Kanal 📢", url="https://t.me/ht_bots"),
        types.InlineKeyboardButton(text="Dəstək 👥", url="https://t.me/ht_bots_chat")
    )
    await message.answer(
        f"🤖 **HT-Security Premium Bot**\n\n👤 **Sahib:** @kullaniciadidi\n🛠 **Status:** Aktiv\n\nQrupda kömək üçün `/help` yazın.",
        reply_markup=builder.as_markup()
    )

@dp.message(Command("admin"))
async def promote_admin(message: types.Message, command: CommandObject):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return await message.answer("İstifadəçini reply edin.")
    title = command.args if command.args else "Admin"
    user = message.reply_to_message.from_user
    try:
        await bot.promote_chat_member(message.chat.id, user.id, can_delete_messages=True, can_restrict_members=True, can_invite_users=True, can_pin_messages=True)
        await bot.set_chat_administrator_custom_title(message.chat.id, user.id, title)
        await message.answer(f"✅ {user.first_name} indi **{title}**!")
    except: await message.answer("❌ Yetkim çatmadı.")

@dp.message(Command("stiker"))
async def st_toggle(message: types.Message, command: CommandObject):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not command.args: return await message.answer("İstifadə: `/stiker off` (bağlamaq) və ya `/stiker on` (açmaq)")
    
    status = (command.args.lower() == "off")
    if message.chat.id not in group_settings: group_settings[message.chat.id] = {}
    group_settings[message.chat.id]["sticker_block"] = status
    await message.answer(f"🚫 Stiker bloku: {'**Aktiv** (Silinir)' if status else '**Deaktiv** (İcazəli)'}")

@dp.message(Command("purge"))
async def purge_msgs(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    for i in range(message.reply_to_message.message_id, message.message_id + 1):
        try: await bot.delete_message(message.chat.id, i)
        except: continue

@dp.message(Command("newfed"))
async def new_fed(message: types.Message, command: CommandObject):
    if not command.args: return
    fed_id = str(abs(hash(command.args)) % 100000)
    fed_db[fed_id] = {"name": command.args, "owner": message.from_user.id, "admins": set(), "banned_users": set()}
    await message.answer(f"✅ **Fed Yaradıldı!**\nAd: {command.args}\nID: `{fed_id}`")

@dp.message(Command("joinfed"))
async def join_fed(message: types.Message, command: CommandObject):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if command.args in fed_db:
        group_feds[message.chat.id] = command.args
        await message.answer(f"🔗 Qrup **{fed_db[command.args]['name']}** federasiyasına bağlandı.")

@dp.message(Command("ban"))
async def ban_user(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    try:
        await bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
        await message.answer(f"✈️ {message.reply_to_message.from_user.first_name} qovuldu.")
    except: pass

@dp.message(Command("mute"))
async def mute_user(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    try:
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, permissions=types.ChatPermissions(can_send_messages=False))
        await message.answer(f"🤐 {message.reply_to_message.from_user.first_name} səssizə alındı.")
    except: pass

@dp.message(Command("unmute"))
async def unmute_user(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    try:
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, permissions=types.ChatPermissions(can_send_messages=True, can_send_other_messages=True))
        await message.answer(f"🔊 {message.reply_to_message.from_user.first_name} danışa bilər.")
    except: pass

@dp.message(Command("reload"))
async def reload_cmd(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    await message.answer("🔄 Sazlamalar yeniləndi.")

@dp.message(F.new_chat_members)
async def on_join(message: types.Message):
    fed_id = group_feds.get(message.chat.id)
    for user in message.new_chat_members:
        if fed_id and user.id in fed_db[fed_id]["banned_users"]:
            await bot.ban_chat_member(message.chat.id, user.id)
            continue
        await message.answer(f"Xoş gəldin, {user.first_name}!")

# --- BOTUN İŞƏ SALINMASI ---
async def main():
    # allowed_updates mütləqdir ki, stikerləri hər zaman görsün
    await dp.start_polling(bot, allowed_updates=["message", "chat_member", "callback_query"])

if __name__ == '__main__':
    asyncio.run(main())
