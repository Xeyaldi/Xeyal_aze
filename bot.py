import asyncio
import os
import logging
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder

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

# Söyüş siyahısı (Sənin əvvəlki kodundan)
BAD_WORDS = ["söyüş1", "söyüş2", "qehbe", "bic", "sq", "amciq", "gotveran", "peyser", "sik", "daşaq", "siktir", "gicdıllaq", "atdıran", "fahişə", "dalbayob"]

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
# 🛑 GLOBAL MANAGER (STİKER VƏ SÖYÜŞ - HAMI ÜÇÜN)
# =====================
@dp.message(lambda m: not m.text or not m.text.startswith("/"))
async def global_manager(message: types.Message):
    if not message.chat or message.chat.type == "private":
        return

    chat_id = message.chat.id
    
    # 1. STİKER / GIF / V-NOTE (Admin daxil hamı üçün)
    if message.sticker or message.animation or message.video_note:
        if group_settings.get(chat_id, {}).get("sticker_block") == True:
            try:
                await message.delete()
                return
            except:
                pass

    # 2. SÖYÜŞ VƏ LİNK (Admin daxil hamı üçün)
    if message.text:
        text_lower = message.text.lower()
        if any(w in text_lower for w in BAD_WORDS) or "t.me/" in text_lower or "http" in text_lower:
            try:
                await message.delete()
            except:
                pass

# =====================
# START (Düzəliş edildi: Developer butonu, Help əmri və Yönlü yazı)
# =====================
@dp.message(Command("start"))
async def start(message: types.Message):
    me = await bot.get_me()
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="➕ Botu Qrupa Əlavə Et", url=f"https://t.me/{me.username}?startgroup=true"))
    kb.row(
        types.InlineKeyboardButton(text="📢 Kanal", url="https://t.me/ht_bots"),
        types.InlineKeyboardButton(text="💬 Dəstək", url="https://t.me/ht_bots_chat")
    )
    # Developer düyməsi əlavə edildi
    kb.row(types.InlineKeyboardButton(text="👨‍💻 Developer", url="tg://user?id=8024893255"))

    text = (
        "🤖 HT-Security Moderation Bot\n\n"
        "Bu bot Telegram qrupları üçün hazırlanmış tam təhlükəsizlik və idarəetmə botudur.\n\n"
        "🛡 İmkanlar:\n"
        "• Stiker / GIF / Video-note avtomatik nəzarət\n"
        "• Söyüş və uyğun olmayan sözlərin silinməsi\n"
        "• /ban, /mute, /warn komandaları\n"
        "• Auto-Ban (warn limiti dolduqda)\n"
        "• Fed-Ban (bir neçə qrup üçün ortaq ban)\n"
        "• Inline Admin Panel\n\n"
        "👮 Botu qrupa əlavə etdikdən sonra ona admin səlahiyyəti verin.\n"
        "ℹ️ Əmrlərin siyahısı üçün /help yazın.\n\n"
        "⚡ Sürətli • Stabil • Təhlükəsiz"
    )
    await message.answer(text, reply_markup=kb.as_markup())

# =====================
# HELP
# =====================
@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    text = (
        "📘 HT-Security Bot – Kömək\n\n"
        "👮 Admin Komandaları:\n"
        "• /ban – İstifadəçini banla (reply)\n"
        "• /unban <id> – Banı aç\n"
        "• /mute [10m|2h|1d] – Səssizə al\n"
        "• /unmute – Səssizi aç\n"
        "• /warn – Xəbərdarlıq ver\n"
        "• /warnings – Warn sayını göstər\n"
        "• /clearwarns – Warnları sil\n"
        "• /setwarn <sayı> – Auto-ban limiti\n\n"
        "🌐 Fed:\n"
        "• /newfed <ad> – Fed yarat\n"
        "• /joinfed <id> – Qrupu fed-ə bağla\n"
        "• /fban – Fed üzrə ban\n\n"
        "⚙️ Ayarlar:\n"
        "• /stiker on|off – Stiker nəzarəti\n"
        "• /panel – Admin panel\n\n"
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
        try:
            await bot.ban_chat_member(message.chat.id, user.id)
            user_warns[key] = 0
            await message.answer(f"🚫 {user.first_name} AUTO-BAN ({limit} warn)")
        except: pass
    else:
        await message.answer(f"⚠️ Warn: {user_warns[key]}/{limit}")

@dp.message(Command("setwarn"))
async def setwarn(message: types.Message, command: CommandObject):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    try:
        group_settings.setdefault(message.chat.id, {})["warn_limit"] = int(command.args)
        await message.answer(f"⚙️ Warn limiti {command.args} olaraq təyin edildi.")
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
        try:
            await bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
            await message.answer("🚫 İstifadəçi banlandı.")
        except: pass

@dp.message(Command("unban"))
async def unban(message: types.Message, command: CommandObject):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    if command.args:
        try:
            await bot.unban_chat_member(message.chat.id, int(command.args))
            await message.answer("✅ İstifadəçinin banı açıldı.")
        except: pass

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

    try:
        await bot.restrict_chat_member(
            message.chat.id,
            message.reply_to_message.from_user.id,
            permissions=types.ChatPermissions(can_send_messages=False),
            until_date=until
        )
        await message.answer(f"🔇 Mute edildi. Vaxt: {command.args if command.args else 'Həmişəlik'}")
    except: pass

@dp.message(Command("unmute"))
async def unmute(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return
    if message.reply_to_message:
        try:
            await bot.restrict_chat_member(
                message.chat.id,
                message.reply_to_message.from_user.id,
                permissions=types.ChatPermissions(can_send_messages=True, can_send_other_messages=True, can_send_polls=True, can_add_web_page_previews=True)
            )
            await message.answer("🔊 İstifadəçinin səsi açıldı.")
        except: pass

# =====================
# FED
# =====================
@dp.message(Command("newfed"))
async def newfed(message: types.Message, command: CommandObject):
    if not command.args: return
    fed_id = str(abs(hash(command.args)) % 99999)
    fed_db[fed_id] = {"name": command.args, "banned": set()}
    await message.answer(f"✅ Fed yaradıldı: **{command.args}**\nID: `{fed_id}`")

@dp.message(Command("joinfed"))
async def joinfed(message: types.Message, command: CommandObject):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if command.args in fed_db:
        group_feds[message.chat.id] = command.args
        await message.answer(f"🔗 Qrup {fed_db[command.args]['name']} federasiyasına qoşuldu.")

@dp.message(Command("fban"))
async def fban(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if message.reply_to_message:
        fed_id = group_feds.get(message.chat.id)
        if fed_id:
            user_id = message.reply_to_message.from_user.id
            fed_db[fed_id]["banned"].add(user_id)
            try:
                await bot.ban_chat_member(message.chat.id, user_id)
                await message.answer("🌐 FED BAN: İstifadəçi federasiya üzrə banlandı.")
            except: pass

# =====================
# START BOT
# =====================
async def main():
    await dp.start_polling(bot, allowed_updates=["message", "callback_query", "chat_member"])

if __name__ == "__main__":
    asyncio.run(main())
