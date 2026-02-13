import asyncio
import os
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder

# FILTER
from filters.sticker_filter import global_filter

# =====================
# KONFİQ
# =====================
OWNER_ID = 8024893255
API_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# =====================
# DATABASE (RAM)
# =====================
group_settings = {}
user_warns = {}
fed_db = {}
group_feds = {}

# =====================
# ADMİN CHECK
# =====================
async def is_admin(chat_id, user_id):
    if user_id == OWNER_ID:
        return True
    try:
        m = await bot.get_chat_member(chat_id, user_id)
        return m.status in ("administrator", "creator")
    except:
        return False

# =====================
# TIME PARSER
# =====================
def parse_time(t):
    try:
        n = int(t[:-1])
        if t.endswith("m"):
            return timedelta(minutes=n)
        if t.endswith("h"):
            return timedelta(hours=n)
        if t.endswith("d"):
            return timedelta(days=n)
    except:
        return None

# =====================
# FILTER RUNNER
# =====================
@dp.message()
async def run_filters(message: types.Message):
    await global_filter(
        message=message,
        bot=bot,
        is_admin=is_admin,
        group_settings=group_settings
    )

# =====================
# START
# =====================
@dp.message(Command("start"))
async def start(message: types.Message):
    me = await bot.get_me()

    kb = InlineKeyboardBuilder()
    kb.row(
        types.InlineKeyboardButton(
            text="➕ Botu Qrupa Əlavə Et",
            url=f"https://t.me/{me.username}?startgroup=true"
        )
    )
    kb.row(
        types.InlineKeyboardButton(text="📢 Kanal", url="https://t.me/ht_bots"),
        types.InlineKeyboardButton(text="💬 Dəstək", url="https://t.me/ht_bots_chat")
    )

    text = (
        "🤖 **Flower-Qrup kömək botu\n\n"
        "Bu bot Telegram qrupları üçün hazırlanmış **tam təhlükəsizlik və idarəetmə** botudur.\n\n"
        "🛡 İmkanlar:\n"
        "• Stiker / GIF / Video-note avtomatik nəzarət\n"
        "• Söyüş və uyğun olmayan sözlərin silinməsi\n"
        "• `/ban`, `/mute`, `/warn` komandaları\n"
        "• Auto-Ban (warn limiti dolduqda)\n"
        "• Fed-Ban (bir neçə qrup üçün ortaq ban)\n"
        "• Inline Admin Panel\n\n"
        "👮 Botu qrupa əlavə etdikdən sonra ona admin səlahiyyəti verin.\n"
        "ℹ️ Komandalar üçün `/help` yazın.\n\n"
        "⚡ Sürətli • Stabil • Təhlükəsiz"
    )

    await message.answer(text, reply_markup=kb.as_markup())

# =====================
# HELP
# =====================
@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    text = (
        "📘 Flower-Security Bot – Kömək\n\n"
        "👮 Admin Komandaları:\n"
        "• `/ban` – İstifadəçini banla (reply)\n"
        "• `/unban <id>` – Banı aç\n"
        "• `/mute [10m|2h|1d]` – Səssizə al\n"
        "• `/unmute` – Səssizi aç\n"
        "• `/warn` – Xəbərdarlıq ver\n"
        "• `/warnings` – Warn sayını göstər\n"
        "• `/clearwarns` – Warnları sil\n"
        "• `/setwarn <sayı>` – Auto-ban limiti\n\n"
        "🌐 **Fed:**\n"
        "• `/newfed <ad>` – Fed yarat\n"
        "• `/joinfed <id>` – Qrupu fed-ə bağla\n"
        "• `/fban` – Fed üzrə ban\n\n"
        "⚙️ Ayarlar:\n"
        "• `/stiker on|off` – Stiker nəzarəti\n"
        "• `/panel` – Admin panel\n\n"
        "ℹ️ Botun işləməsi üçün admin icazəsi lazımdır."
    )
    await message.answer(text)

# =====================
# STİKER ON / OFF
# =====================
@dp.message(Command("stiker"))
async def stiker(message: types.Message, command: CommandObject):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    if not command.args:
        return await message.answer("/stiker on | off")

    state = command.args.lower() == "off"
    group_settings.setdefault(message.chat.id, {})["sticker_block"] = state
    await message.answer(f"🚫 Stiker bloku: {'AKTİV' if state else 'DEAKTİV'}")

# =====================
# WARN + AUTO BAN
# =====================
@dp.message(Command("warn"))
async def warn(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        return

    user = message.reply_to_message.from_user
    key = (message.chat.id, user.id)
    user_warns[key] = user_warns.get(key, 0) + 1

    limit = group_settings.get(message.chat.id, {}).get("warn_limit", 3)

    if user_warns[key] >= limit:
        await bot.ban_chat_member(message.chat.id, user.id)
        user_warns[key] = 0
        await message.answer(f"🚫 {user.first_name} AUTO-BAN ({limit} warn)")
    else:
        await message.answer(f"⚠️ Warn: {user_warns[key]}/{limit}")

@dp.message(Command("setwarn"))
async def setwarn(message: types.Message, command: CommandObject):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    try:
        group_settings.setdefault(message.chat.id, {})["warn_limit"] = int(command.args)
        await message.answer("⚙️ Warn limiti dəyişdirildi")
    except:
        await message.answer("/setwarn 3")

# =====================
# BAN / UNBAN
# =====================
@dp.message(Command("ban"))
async def ban(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    if message.reply_to_message:
        await bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
        await message.answer("🚫 Banlandı")

@dp.message(Command("unban"))
async def unban(message: types.Message, command: CommandObject):
    if await is_admin(message.chat.id, message.from_user.id):
        try:
            await bot.unban_chat_member(message.chat.id, int(command.args))
            await message.answer("✅ Unban")
        except:
            pass

# =====================
# MUTE / UNMUTE
# =====================
@dp.message(Command("mute"))
async def mute(message: types.Message, command: CommandObject):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        return

    duration = parse_time(command.args) if command.args else None
    until = datetime.now() + duration if duration else None

    await bot.restrict_chat_member(
        message.chat.id,
        message.reply_to_message.from_user.id,
        permissions=types.ChatPermissions(can_send_messages=False),
        until_date=until
    )
    await message.answer("🔇 Mute edildi")

@dp.message(Command("unmute"))
async def unmute(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    if message.reply_to_message:
        await bot.restrict_chat_member(
            message.chat.id,
            message.reply_to_message.from_user.id,
            permissions=types.ChatPermissions(can_send_messages=True)
        )
        await message.answer("🔊 Unmute")

# =====================
# FED
# =====================
@dp.message(Command("newfed"))
async def newfed(message: types.Message, command: CommandObject):
    fed_id = str(abs(hash(command.args)) % 99999)
    fed_db[fed_id] = {"banned": set()}
    await message.answer(f"✅ Fed yaradıldı\nID: `{fed_id}`")

@dp.message(Command("joinfed"))
async def joinfed(message: types.Message, command: CommandObject):
    if command.args in fed_db:
        group_feds[message.chat.id] = command.args
        await message.answer("🔗 Fed qoşuldu")

@dp.message(Command("fban"))
async def fban(message: types.Message):
    if message.reply_to_message:
        fed_id = group_feds.get(message.chat.id)
        if fed_id:
            user_id = message.reply_to_message.from_user.id
            fed_db[fed_id]["banned"].add(user_id)
            await bot.ban_chat_member(message.chat.id, user_id)
            await message.answer("🌐 FED BAN")

# =====================
# START BOT
# =====================
async def main():
    await dp.start_polling(bot, allowed_updates=["message", "callback_query", "chat_member"])

if __name__ == "__main__":
    asyncio.run(main())
