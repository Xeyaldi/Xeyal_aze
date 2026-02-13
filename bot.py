import asyncio
import os
from datetime import datetime, timedelta

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
    if user_id == OWNER_ID:
        return True
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ["administrator", "creator"]
    except:
        return False

# --- VAxt parseri (mute üçün) ---
def parse_time(time_str):
    try:
        num = int(time_str[:-1])
        unit = time_str[-1]
        if unit == "m":
            return timedelta(minutes=num)
        if unit == "h":
            return timedelta(hours=num)
        if unit == "d":
            return timedelta(days=num)
    except:
        return None

# --- 🛑 QƏTİ SİLİNƏN MƏNTİQ (TOXUNULMAYIB) ---
@dp.message(lambda m: not m.text or any(x in (m.text or "").lower() for x in BAD_WORDS) or m.sticker or m.animation)
async def global_filter(message: types.Message):
    chat_id = message.chat.id
    if message.chat.type == "private":
        return

    if not await is_admin(chat_id, message.from_user.id):
        if group_settings.get(chat_id, {}).get("sticker_block", False):
            if message.sticker or message.animation or message.video_note:
                try:
                    return await message.delete()
                except:
                    pass

        if message.text:
            if any(word in message.text.lower() for word in BAD_WORDS):
                try:
                    return await message.delete()
                except:
                    pass

# --- START ---
@dp.message(Command("start"))
async def start(message: types.Message):
    kb = InlineKeyboardBuilder()
    kb.row(
        types.InlineKeyboardButton(
            text="Məni Qrupa Əlavə Et ➕",
            url=f"https://t.me/{(await bot.get_me()).username}?startgroup=true"
        )
    )
    await message.answer("🤖 **HT-Security Bot**\n\nQrup üçün `/help` yaz.", reply_markup=kb.as_markup())

# --- STİKER AÇ / BAĞLA ---
@dp.message(Command("stiker"))
async def st_toggle(message: types.Message, command: CommandObject):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    if not command.args:
        return await message.answer("İstifadə: `/stiker on` və ya `/stiker off`")

    status = command.args.lower() == "off"
    group_settings.setdefault(message.chat.id, {})["sticker_block"] = status
    await message.answer(f"🚫 Stiker bloku: {'AKTİV' if status else 'DEAKTİV'}")

# ======================
# 🔨 ADMİN KOMANDALARI
# ======================

# --- /ban ---
@dp.message(Command("ban"))
async def ban_user(message: types.Message, command: CommandObject):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        return await message.answer("İstifadəçini reply et.")

    reason = command.args or "Səbəb yoxdur"
    user = message.reply_to_message.from_user

    try:
        await bot.ban_chat_member(message.chat.id, user.id)
        await message.answer(
            f"🚫 **BAN**\n"
            f"👤 {user.first_name}\n"
            f"👮 {message.from_user.first_name}\n"
            f"📄 {reason}"
        )
    except:
        await message.answer("❌ Ban alınmadı.")

# --- /unban ---
@dp.message(Command("unban"))
async def unban_user(message: types.Message, command: CommandObject):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    if not command.args:
        return await message.answer("İstifadə: `/unban user_id`")

    try:
        await bot.unban_chat_member(message.chat.id, int(command.args))
        await message.answer("✅ Unban edildi.")
    except:
        await message.answer("❌ Unban mümkün olmadı.")

# --- /mute ---
@dp.message(Command("mute"))
async def mute_user(message: types.Message, command: CommandObject):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        return await message.answer("İstifadəçini reply et.")

    args = command.args.split() if command.args else []
    duration = parse_time(args[0]) if args else None
    reason = " ".join(args[1:]) if duration and len(args) > 1 else "Səbəb yoxdur"

    until_date = datetime.now() + duration if duration else None
    user = message.reply_to_message.from_user

    try:
        await bot.restrict_chat_member(
            message.chat.id,
            user.id,
            permissions=types.ChatPermissions(can_send_messages=False),
            until_date=until_date
        )
        await message.answer(
            f"🔇 **MUTE**\n"
            f"👤 {user.first_name}\n"
            f"⏱ {args[0] if duration else 'Limitsiz'}\n"
            f"📄 {reason}"
        )
    except:
        await message.answer("❌ Mute alınmadı.")

# --- /unmute ---
@dp.message(Command("unmute"))
async def unmute_user(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        return await message.answer("İstifadəçini reply et.")

    user = message.reply_to_message.from_user
    try:
        await bot.restrict_chat_member(
            message.chat.id,
            user.id,
            permissions=types.ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )
        await message.answer(f"🔊 {user.first_name} artıq danışa bilər.")
    except:
        await message.answer("❌ Unmute alınmadı.")

# --- JOIN CHECK ---
@dp.message(F.new_chat_members)
async def on_join(message: types.Message):
    fed_id = group_feds.get(message.chat.id)
    for user in message.new_chat_members:
        if fed_id and user.id in fed_db.get(fed_id, {}).get("banned_users", []):
            await bot.ban_chat_member(message.chat.id, user.id)
        else:
            await message.answer(f"Xoş gəldin, {user.first_name}!")

# --- BOT START ---
async def main():
    await dp.start_polling(bot, allowed_updates=["message", "chat_member", "callback_query"])

if __name__ == "__main__":
    asyncio.run(main())
