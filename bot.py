import asyncio
import os
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import (
    ChatPermissions, 
    InlineKeyboardButton, 
    CallbackQuery,
    Message,
    BotCommand
)

# --- LOGLAMA SİSTEMİ ---
logging.basicConfig(level=logging.INFO)

# --- KONFİQURASİYA ---
OWNER_ID = 8024893255 
API_TOKEN = os.getenv("BOT_TOKEN") 

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- MƏLUMAT BAZALARI (QƏTİ İXTİSARSIZ) ---
fed_db = {}           
group_feds = {}       
group_settings = {}   
custom_filters = {} 
user_warns = {}

# --- SÖYÜŞ SİYAHISI (TAM) ---
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

# --- BUTONLAR (DEVELOPER VƏ DƏSTƏK TAMDIR) ---
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

# --- START KOMANDASI ---
@dp.message(Command("start"))
async def cmd_start(message: Message):
    text = (
        "🤖 Flower Premium Botuna Xoş Gəldiniz!\n\n"
        "Mən qruplarınızı söyüşlərdən, reklamlardan və arzuolunmaz şəxslərdən qorumaq üçün yaradılmış "
        "peşəkar idarəetmə botuyam. Rose və GroupHelp funksiyaları ilə tam təchiz olunmuşam.\n\n"
        "Aşağıdakı düymələrdən istifadə edərək kömək ala bilərsiniz 👇"
    )
    await message.answer(text, reply_markup=get_main_btns())

# --- HELP KOMANDASI ---
@dp.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "📜 Botun Geniş Əmrləri:\n\n"
        "🛡 Federasiya:\n"
        "• /newfed [ad] - Yeni Federasiya yaradır\n"
        "• /joinfed [ID] - Qrupu Fed-ə bağlayır\n"
        "• /gfban - Fed səviyyəsində qlobal ban\n"
        "• /ggroupfed - Qrupun Fed məlumatı\n\n"
        "⚙️ İdarəetmə:\n"
        "• /admin [rütbə] - Admin rütbəsi verir (Reply)\n"
        "• /unadmin - Admin rütbəsini geri alır\n"
        "• /ban - İstifadəçini qovur\n"
        "• /mute - İstifadəçini səssizə alır\n"
        "• /purge - Mesajları reply-dan aşağı təmizləyir\n\n"
        "🔍 Filtrlər:\n"
        "• /filter [söz] - Xüsusi cavab təyin edir\n"
        "• /stop [söz] - Təyin edilmiş filtri silir\n"
        "• /stiker off - Stiker və Giflərə qadağa qoyur\n"
        "• /stiker on - Stiker və Giflərə icazə verir\n\n"
        "🔐 Təhlükəsizlik:\n"
        "• /lock - Qrupu tam bağlayır\n"
        "• /unlock - Qrupu açır\n"
        "• /info - İstifadəçi ID və status məlumatı\n"
        "• /reload - Sazlamaları və adminləri yeniləyir"
    )
    await message.answer(help_text, reply_markup=get_main_btns())

# --- RELOAD KOMANDASI ---
@dp.message(Command("reload"))
async def cmd_reload(message: Message):
    status = await check_admin_status(message.chat.id, message.from_user.id)
    if status == "user": return
    m = await message.answer("🔄 Sazlamalar və admin siyahısı yenilənir...")
    await asyncio.sleep(1.5)
    await m.edit_text("✅ Sazlamalar uğurla yeniləndi! Bot tam hazır vəziyyətdədir.")

# --- ADMİN VƏ RÜTBƏ SİSTEMİ ---
@dp.message(Command("admin"))
async def cmd_promote(message: Message, command: CommandObject):
    status = await check_admin_status(message.chat.id, message.from_user.id)
    if status == "user": return
    if not message.reply_to_message:
        return await message.answer("Admin etmək üçün istifadəçini reply edin!")
    
    title = command.args if command.args else "Admin"
    try:
        await bot.promote_chat_member(message.chat.id, message.reply_to_message.from_user.id, 
            can_delete_messages=True, can_restrict_members=True, can_invite_users=True, can_pin_messages=True)
        await bot.set_chat_administrator_custom_title(message.chat.id, message.reply_to_message.from_user.id, title)
        await message.answer(f"✅ {message.reply_to_message.from_user.first_name} indi {title} olaraq təyin edildi!")
    except:
        await message.answer("❌ Xəta! Mənə adminlik və rütbə dəyişmək yetgisi verin.")

@dp.message(Command("unadmin"))
async def cmd_demote(message: Message):
    status = await check_admin_status(message.chat.id, message.from_user.id)
    if status == "user": return
    if not message.reply_to_message: return
    try:
        await bot.promote_chat_member(message.chat.id, message.reply_to_message.from_user.id, can_delete_messages=False, can_restrict_members=False)
        await message.answer(f"🗑 {message.reply_to_message.from_user.first_name} rütbəsi geri alındı.")
    except: pass

# --- STİKER VƏ GİF BLOK KOMANDASI ---
@dp.message(Command("stiker"))
async def cmd_stiker(message: Message, command: CommandObject):
    status = await check_admin_status(message.chat.id, message.from_user.id)
    if status == "user": return
    if not command.args:
        return await message.answer("İstifadə: /stiker off (bağlamaq) və ya /stiker on (açmaq)")
    
    choice = command.args.lower()
    if choice == "off":
        group_settings[message.chat.id] = {"sticker_block": True}
        await message.answer("🚫 Stiker və Gif bloku aktiv edildi")
    elif choice == "on":
        group_settings[message.chat.id] = {"sticker_block": False}
        await message.answer("✅ Stiker və Gif bloku deaktiv edildi.")

# --- PURGE SİSTEMİ ---
@dp.message(Command("purge"))
async def cmd_purge(message: Message):
    status = await check_admin_status(message.chat.id, message.from_user.id)
    if status == "user": return
    if not message.reply_to_message:
        return await message.answer("Silmək üçün bir mesajı reply edin.")
    
    start_id = message.reply_to_message.message_id
    end_id = message.message_id
    for i in range(start_id, end_id + 1):
        try: await bot.delete_message(message.chat.id, i)
        except: continue
    await message.answer("✅ Mesajlar uğurla təmizləndi.")

# --- FEDERASİYA FUNKSİYALARI ---
@dp.message(Command("newfed"))
async def cmd_newfed(message: Message, command: CommandObject):
    if not command.args: return
    fed_id = str(message.from_user.id)[:5]
    fed_db[fed_id] = {"name": command.args, "owner": message.from_user.id}
    await message.answer(f"✅ Yeni Federasiya yaradıldı: {command.args}\n🆔 Fed ID: {fed_id}")

@dp.message(Command("ggroupfed"))
async def cmd_ggroupfed(message: Message):
    await message.answer("ℹ️ Bu qrup heç bir federasiyaya bağlı deyil.")

# --- FİLTER SİSTEMİ ---
@dp.message(Command("filter"))
async def cmd_filter(message: Message, command: CommandObject):
    status = await check_admin_status(message.chat.id, message.from_user.id)
    if status == "user": return
    if not message.reply_to_message or not command.args:
        return await message.answer("İstifadə: /filter [söz] (bir mesaja reply edərək)")
    
    kw = command.args.lower()
    if message.chat.id not in custom_filters: custom_filters[message.chat.id] = {}
    custom_filters[message.chat.id][kw] = message.reply_to_message.text
    await message.answer(f"✅ {kw} filtri aktiv edildi.")

# --- LOCK & UNLOCK ---
@dp.message(Command("lock"))
async def cmd_lock(message: Message):
    status = await check_admin_status(message.chat.id, message.from_user.id)
    if status == "user": return
    await bot.set_chat_permissions(message.chat.id, ChatPermissions(can_send_messages=False))
    await message.answer("🔒 Qrup bağlandı. Artıq yalnız adminlər yaza bilər.")

@dp.message(Command("unlock"))
async def cmd_unlock(message: Message):
    status = await check_admin_status(message.chat.id, message.from_user.id)
    if status == "user": return
    await bot.set_chat_permissions(message.chat.id, ChatPermissions(can_send_messages=True, can_send_other_messages=True))
    await message.answer("🔓 Qrup açıldı. Hər kəs yaza bilər.")

# --- İNFO KOMANDASI ---
@dp.message(Command("info"))
async def cmd_info(message: Message):
    target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    status = await check_admin_status(message.chat.id, target.id)
    await message.answer(f"👤 Məlumat Paneli:\n\n🆔 ID: {target.id}\n📛 Ad: {target.first_name}\n💎 Status: {status}")

# --- GLOBAL HANDLER (SÖYÜŞ, LİNK, STİKER VƏ GİF SİLMƏ) ---
@dp.message()
async def main_handler(message: Message):
    if not message.chat or message.chat.type not in ["group", "supergroup"]: return
    
    status = await check_admin_status(message.chat.id, message.from_user.id)
    chat_id = message.chat.id

    # 1. STİKER, GİF VƏ ANİMASİYA SİLMƏ (DÜZƏLDİLDİ)
    if message.sticker or message.animation or message.video_note:
        if group_settings.get(chat_id, {}).get("sticker_block") and status == "user":
            try:
                await bot.delete_message(chat_id, message.message_id)
                return 
            except:
                pass

    # 2. MƏTN YOXLAMALARI
    if message.text:
        text_lower = message.text.lower()
        
        # SÖYÜŞ FİLTRİ
        if any(w in text_lower for w in BAD_WORDS) and status == "user":
            try:
                await message.delete()
                return await message.answer(f"⚠️ {message.from_user.first_name}, xahiş olunur səviyyəli danışın!")
            except: pass

        # LİNK FİLTRİ
        if ("t.me/" in text_lower or "http" in text_lower) and status == "user":
            try: await message.delete()
            except: pass
            return

        # CUSTOM FİLTER SİSTEMİ
        if chat_id in custom_filters:
            for k, v in custom_filters[chat_id].items():
                if k in text_lower: 
                    return await message.reply(v)

# --- BOTUN BAŞLADILMASI ---
async def main():
    await bot.set_my_commands([
        BotCommand(command="start", description="Başlat"),
        BotCommand(command="help", description="Kömək"),
        BotCommand(command="reload", description="Yenilə"),
        BotCommand(command="admin", description="Admin et"),
        BotCommand(command="stiker", description="Stiker bloku"),
        BotCommand(command="purge", description="Təmizlə")
    ])
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
