import asyncio
import os
import logging
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest

# =====================
# KONFİQURASİYA
# =====================
OWNER_ID = 8024893255
API_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# =====================
# MƏLUMAT BAZASI (RAM)
# =====================
group_settings = {}
user_warns = {}
fed_db = {}
group_feds = {}
user_scores = {"total": {}, "daily": {}, "weekly": {}, "monthly": {}}
user_names = {}
group_rules = {}

# Söyüş siyahısı
BAD_WORDS = ["söyüş1", "söyüş2", "qehbe", "bic", "sq", "amciq", "gotveran", "peyser", "sik", "daşaq", "siktir", "gicdıllaq", "atdıran", "fahişə", "dalbayob"]

# =====================
# KÖMƏKÇİ FUNKSİYALAR (İCAZƏLƏR)
# =====================
async def is_admin(chat_id, user_id):
    if user_id == OWNER_ID: return True
    try:
        m = await bot.get_chat_member(chat_id, user_id)
        return m.status in ("administrator", "creator")
    except: return False

async def is_creator_or_owner(chat_id, user_id):
    if user_id == OWNER_ID: return True
    try:
        m = await bot.get_chat_member(chat_id, user_id)
        return m.status == "creator"
    except: return False

def parse_time(t):
    try:
        n = int(t[:-1])
        if t.endswith("m"): return timedelta(minutes=n)
        if t.endswith("h"): return timedelta(hours=n)
        if t.endswith("d"): return timedelta(days=n)
    except: return None

# =====================
# QLOBAL MENECER (SÖYÜŞ, LİNK, STİKER VƏ SAYĞAC)
# =====================
@dp.message(lambda m: not m.text or not m.text.startswith("/"))
async def global_manager(message: types.Message):
    if not message.chat or message.chat.type == "private": return

    chat_id = message.chat.id
    user_id = message.from_user.id
    user_names[user_id] = message.from_user.first_name

    # Statistika sayğacı (Hər kəs üçün)
    for cat in ["total", "daily", "weekly", "monthly"]:
        key = (chat_id, user_id)
        user_scores[cat][key] = user_scores[cat].get(key, 0) + 1

    # Mesaj limit bildirişləri
    total_score = user_scores["total"][(chat_id, user_id)]
    if total_score == 200:
        await message.reply(f"🎉 Təbriklər {message.from_user.first_name}! Artıq 200 mesaj yazdınız.")
    elif total_score == 1000:
        await message.reply(f"🏆 Möhtəşəm! {message.from_user.first_name}, 1000 mesaj limitinə çatdınız!")

    # 1. STİKER / GIF / V-NOTE QORUMASI (Aktivdirsə hamını silir)
    if message.sticker or message.animation or message.video_note:
        if group_settings.get(chat_id, {}).get("sticker_block") == True:
            try:
                await message.delete()
                return
            except: pass

    # 2. SÖYÜŞ VƏ LİNK QORUMASI
    if message.text:
        text_lower = message.text.lower()
        if any(w in text_lower for w in BAD_WORDS) or "t.me/" in text_lower or "http" in text_lower:
            try: await message.delete()
            except: pass

# =====================
# TOPMESAJ (MESSAGE SCOR STYLE)
# =====================
@dp.message(Command("topmesaj"))
async def top_menu(message: types.Message):
    kb = InlineKeyboardBuilder()
    kb.row(
        types.InlineKeyboardButton(text="📆 Günlük", callback_data="top_daily"),
        types.InlineKeyboardButton(text="📆 Haftalık", callback_data="top_weekly"),
        types.InlineKeyboardButton(text="📆 Aylık", callback_data="top_monthly")
    )
    kb.row(types.InlineKeyboardButton(text="📊 Bütün zamanlarda", callback_data="top_total"))
    
    text = (f"Message Scor 🇦🇿\n👤 {message.from_user.first_name}\n/topmesaj\n\n"
            f"👥 Bulunduğunuz grup için sıralama türünü seçiniz.")
    await message.answer(text, reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("top_"))
async def process_top_callback(callback: types.CallbackQuery):
    category = callback.data.split("_")[1]
    chat_id = callback.message.chat.id
    scores = {k[1]: v for k, v in user_scores[category].items() if k[0] == chat_id}
    
    if not scores:
        await callback.answer("Hələ ki məlumat yoxdur.", show_alert=True)
        return

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:13]
    titles = {"daily": "Günlük", "weekly": "Həftəlik", "monthly": "Aylıq", "total": "Bütün zamanlar"}
    
    report = f"📊 {titles[category]} Top 13 Siyahısı:\n\n"
    for i, (u_id, count) in enumerate(sorted_scores, 1):
        name = user_names.get(u_id, f"İstifadəçi {u_id}")
        report += f"{i}. {name} — {count} mesaj\n"
    
    await callback.message.edit_text(report)

# =====================
# ADMİN YETKİSİ VER/AL
# =====================
@dp.message(Command("promote"))
async def promote(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return await message.answer("Yetki vermək üçün mesajı cavablayın.")
    try:
        await bot.promote_chat_member(
            chat_id=message.chat.id,
            user_id=message.reply_to_message.from_user.id,
            can_manage_chat=True, can_delete_messages=True, can_restrict_members=True,
            can_invite_users=True, can_pin_messages=True, can_promote_members=False
        )
        await message.answer(f"✅ {message.reply_to_message.from_user.first_name} admin edildi!")
    except Exception as e: await message.answer(f"Xəta: {e}")

@dp.message(Command("demote"))
async def demote(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    try:
        await bot.promote_chat_member(
            chat_id=message.chat.id,
            user_id=message.reply_to_message.from_user.id,
            can_manage_chat=False, can_delete_messages=False, can_restrict_members=False
        )
        await message.answer(f"❌ {message.reply_to_message.from_user.first_name} adminliyi alındı.")
    except Exception as e: await message.answer(f"Xəta: {e}")

# =====================
# MODERASİYA (BAN, MUTE, WARN)
# =====================
@dp.message(Command("ban"))
async def ban(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if message.reply_to_message:
        try:
            await bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
            await message.answer("🚫 İstifadəçi qrupdan kənarlaşdırıldı.")
        except: await message.answer("Xəta: Admini banlamaq olmaz.")

@dp.message(Command("unban"))
async def unban(message: types.Message, command: CommandObject):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if command.args:
        try:
            await bot.unban_chat_member(message.chat.id, int(command.args))
            await message.answer("✅ İstifadəçinin banı açıldı.")
        except: pass

@dp.message(Command("mute"))
async def mute(message: types.Message, command: CommandObject):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    duration = parse_time(command.args) if command.args else None
    until = datetime.now() + duration if duration else None
    try:
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, permissions=types.ChatPermissions(can_send_messages=False), until_date=until)
        await message.answer(f"🔇 Səssizə alındı: {command.args if command.args else 'Həmişəlik'}")
    except: pass

@dp.message(Command("unmute"))
async def unmute(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if message.reply_to_message:
        try:
            await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, permissions=types.ChatPermissions(can_send_messages=True, can_send_other_messages=True, can_send_polls=True, can_add_web_page_previews=True))
            await message.answer("🔊 Səsi açıldı.")
        except: pass

@dp.message(Command("warn"))
async def warn(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
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
    else: await message.answer(f"⚠️ Xəbərdarlıq: {user_warns[key]}/{limit}")

@dp.message(Command("setwarn"))
async def setwarn(message: types.Message, command: CommandObject):
    if not await is_admin(message.chat.id, message.from_user.id): return
    try:
        group_settings.setdefault(message.chat.id, {})["warn_limit"] = int(command.args)
        await message.answer(f"⚙️ Warn limiti {command.args} olaraq təyin edildi.")
    except: await message.answer("/setwarn 3")

# =====================
# FEDERASİYA
# =====================
@dp.message(Command("newfed"))
async def newfed(message: types.Message, command: CommandObject):
    if not command.args: return
    fed_id = str(abs(hash(command.args)) % 99999)
    fed_db[fed_id] = {"name": command.args, "banned": set()}
    await message.answer(f"✅ Yeni FED: {command.args}\nID: {fed_id}")

@dp.message(Command("joinfed"))
async def joinfed(message: types.Message, command: CommandObject):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if command.args in fed_db:
        group_feds[message.chat.id] = command.args
        await message.answer("🔗 Federasiyaya qoşulma uğurludur.")

@dp.message(Command("fban"))
async def fban(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if message.reply_to_message:
        fed_id = group_feds.get(message.chat.id)
        if fed_id:
            user_id = message.reply_to_message.from_user.id
            fed_db[fed_id]["banned"].add(user_id)
            try: await bot.ban_chat_member(message.chat.id, user_id)
            except: pass
            await message.answer("🌐 FED BAN sistemi ilə uzaqlaşdırıldı.")

# =====================
# AYARLAR (KURUCU VƏ OWNER)
# =====================
@dp.message(Command("stiker"))
async def stiker(message: types.Message, command: CommandObject):
    if not await is_creator_or_owner(message.chat.id, message.from_user.id):
        return await message.answer("❌ Bu əmri sadəcə qrup yaradıcısı və ya bot sahibi işlədə bilər!")
    if not command.args: return await message.answer("/stiker on | off")
    state = command.args.lower() == "off"
    group_settings.setdefault(message.chat.id, {})["sticker_block"] = state
    await message.answer(f"🚫 Stiker bloku: {'AKTİV' if state else 'DEAKTİV'}\n(Aktiv olduqda hər kəsin stikeri silinir)")

# =====================
# ƏLAVƏ FUNKSİYALAR
# =====================
@dp.message(Command("info"))
async def info_cmd(message: types.Message):
    target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    warns = user_warns.get((message.chat.id, target.id), 0)
    score = user_scores["total"].get((message.chat.id, target.id), 0)
    text = (f"👤 İstifadəçi Məlumatı\n\nAd: {target.first_name}\nID: {target.id}\nMesaj Sayı: {score}\nXəbərdarlıq: {warns}")
    await message.answer(text)

@dp.message(Command("setrules"))
async def set_rules(message: types.Message, command: CommandObject):
    if not await is_creator_or_owner(message.chat.id, message.from_user.id):
        return await message.answer("❌ Qaydaları yalnız kurucu təyin edə bilər.")
    if not command.args: return await message.answer("İstifadə: /setrules qaydalar mətni")
    group_rules[message.chat.id] = command.args
    await message.answer("✅ Qrup qaydaları yadda saxlanıldı.")

@dp.message(Command("rules"))
async def get_rules(message: types.Message):
    rules = group_rules.get(message.chat.id, "Bu qrup üçün qayda təyin edilməyib.")
    await message.answer(f"📋 Qrup Qaydaları:\n\n{rules}")

@dp.message(Command("purge"))
async def purge_msgs(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return await message.answer("Təmizləmək üçün bir mesajı reply edin.")
    start_id = message.reply_to_message.message_id
    end_id = message.message_id
    for msg_id in range(start_id, end_id + 1):
        try: await bot.delete_message(message.chat.id, msg_id)
        except: pass

@dp.message(Command("dice"))
async def roll_dice(message: types.Message):
    await bot.send_dice(message.chat.id, emoji="🎲")

@dp.message(Command("stats"))
async def get_stats(message: types.Message):
    total = user_scores["total"].get((message.chat.id, message.from_user.id), 0)
    await message.answer(f"📊 {message.from_user.first_name}, ümumi mesaj sayınız: {total}")

# =====================
# FLOWER-SECURITY START MESAJI
# =====================
@dp.message(Command("start"))
async def start(message: types.Message):
    me = await bot.get_me()
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="➕ Botu Qrupa Əlavə Et", url=f"https://t.me/{me.username}?startgroup=true"))
    kb.row(types.InlineKeyboardButton(text="📢 Kanal", url="https://t.me/ht_bots"), types.InlineKeyboardButton(text="💬 Dəstək", url="https://t.me/ht_bots_chat"))
    kb.row(types.InlineKeyboardButton(text="👤 Developer", url="tg://user?id=8024893255"))
    
    text = (
        "🤖 Flower-Security Qrup idarə Botu\n\n"
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

@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    text = (
        "📘 Flower-Security Bot Kömək\n\n"
        "👮 Admin:\n"
        "/promote, /demote, /ban, /unban, /mute, /unmute, /warn, /purge\n\n"
        "📊 Statistika:\n"
        "/topmesaj, /stats, /info\n\n"
        "⚙️ Ayarlar (Kurucu):\n"
        "/stiker on|off, /setrules, /setwarn\n\n"
        "🌐 Federasiya:\n"
        "/newfed, /joinfed, /fban\n\n"
        "🎲 Əyləncə: /dice"
    )
    await message.answer(text)

# =====================
# BOTU BAŞLAT
# =====================
async def main():
    await dp.start_polling(bot, allowed_updates=["message", "callback_query", "chat_member"])

if __name__ == "__main__":
    asyncio.run(main())
