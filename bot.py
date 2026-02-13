import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- AYARLAR ---
OWNER_ID = 8024893255 
API_TOKEN = os.getenv("BOT_TOKEN") 

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Professional Yaddaş Sistemi
fed_db = {}           
group_feds = {}       
group_settings = {}   
BAD_WORDS = ["söyüş1", "söyüş2"] 

# --- KÖMƏKÇİ FUNKSİYA ---
async def is_user_admin(chat_id: int, user_id: int):
    if user_id == OWNER_ID: return True
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ["administrator", "creator"]
    except: return False

# --- ŞƏXSİ MESAJDA QRUP ƏMRLƏRİNƏ QADAĞA ---
GROUP_ONLY = ["ban", "unban", "gfban", "ungfban", "admin", "unadmin", "stiker", "setwelcome", "joinfed", "ggroupfed"]

@dp.message(Command(*GROUP_ONLY), F.chat.type == "private")
async def restrict_private(message: types.Message):
    await message.answer("⚠️ Bu əmr yalnız qruplarda istifadə edilə bilər!")

# --- START & HELP ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Məni Qrupa Əlavə Et ➕", url=f"https://t.me/{(await bot.get_me()).username}?startgroup=true"))
    builder.row(
        types.InlineKeyboardButton(text="Kanal 📢", url="https://t.me/ht_bots"),
        types.InlineKeyboardButton(text="Dəstək 👥", url="https://t.me/ht_bots_chat")
    )
    builder.row(types.InlineKeyboardButton(text="👨‍💻 Developer", url="https://t.me/kullaniciadidi"))
    
    text = (
        "🤖 HT-Security Premium Bot\n\n"
        "Qrupları qorumaq, federasiya sistemini idarə etmək və təhlükəsizliyi təmin etmək üçün yaradılmışam.\n\n"
        "Kömək üçün /help yazın."
    )
    await message.answer(text, reply_markup=builder.as_markup())

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        "📜 Botun Əmrləri:\n\n"
        "🛡 Federasiya:\n"
        "/newfed [ad] - Yeni Fed yaradır\n"
        "/joinfed [id] - Qrupu Fed-ə bağlayır\n"
        "/ggroupfed - Qrupun Fed məlumatını göstərir\n"
        "/gfban - Qlobal ban (Reply)\n"
        "/ungfban - Qlobal banı açır\n\n"
        "⚙️ Qrup İdarəetmə:\n"
        "/admin [rütbə] - Admin edir və rütbə verir\n"
        "/unadmin - Adminliyi geri alır\n"
        "/ban /unban - Qrupdan qovur/açır\n"
        "/stiker off/on - Stikerləri təmizləyir"
    )
    await message.answer(help_text)

# --- ADMİN VƏ UNADMİN SİSTEMİ ---
@dp.message(Command("admin"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_promote(message: types.Message, command: CommandObject):
    if not await is_user_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message:
        return await message.answer("Admin etmək üçün istifadəçini reply edin.")
    
    title = command.args if command.args else "Admin"
    try:
        await bot.promote_chat_member(
            message.chat.id, message.reply_to_message.from_user.id, 
            can_delete_messages=True, can_restrict_members=True, 
            can_invite_users=True, can_pin_messages=True
        )
        await bot.set_chat_administrator_custom_title(message.chat.id, message.reply_to_message.from_user.id, title)
        await message.answer(f"✅ {message.reply_to_message.from_user.first_name} indi **{title}** olaraq təyin edildi!")
    except:
        await message.answer("❌ Xəta! Məni admin edib 'Yeni admin təyin etmək' yetgisi verin.")

@dp.message(Command("unadmin"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_demote(message: types.Message):
    if not await is_user_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    try:
        await bot.promote_chat_member(
            message.chat.id, message.reply_to_message.from_user.id,
            can_delete_messages=False, can_restrict_members=False,
            can_invite_users=False, can_pin_messages=False
        )
        await message.answer(f"🗑 {message.reply_to_message.from_user.first_name} adminlikdən çıxarıldı.")
    except: pass

# --- FEDERASİYA YOXLAMA VƏ GFBAN ---
@dp.message(Command("ggroupfed"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_check_fed(message: types.Message):
    fed_id = group_feds.get(message.chat.id)
    if not fed_id:
        await message.answer("ℹ️ Bu qrup heç bir federasiyaya bağlı deyil.")
    else:
        await message.answer(f"🔗 Bu qrup **{fed_db[fed_id]['name']}** federasiyasına bağlıdır.")

@dp.message(Command("gfban"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_gfban(message: types.Message):
    fed_id = group_feds.get(message.chat.id)
    if not fed_id:
        return await message.answer("❌ Bu qrup federasiyaya qoşulmayıb.")
    
    if message.from_user.id != fed_db[fed_id]["owner"] and message.from_user.id not in fed_db[fed_id].get("admins", set()):
        return await message.answer("❌ Federasiya yetginiz yoxdur.")
        
    if not message.reply_to_message:
        return await message.answer("Ban etmək üçün istifadəçini reply edin.")

    target = message.reply_to_message.from_user.id
    fed_db[fed_id]["banned_users"].add(target)
    try:
        await bot.ban_chat_member(message.chat.id, target)
        await message.answer(f"🌏 GFBAN! {message.reply_to_message.from_user.first_name} qovuldu.")
    except: pass

# --- STİKER KONTROLU (XÜSUSİ HANDLER) ---
@dp.message(Command("stiker"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_stiker(message: types.Message, command: CommandObject):
    if not await is_user_admin(message.chat.id, message.from_user.id): return
    if not command.args:
        return await message.answer("İstifadə: `/stiker off` və ya `/stiker on`")
    
    status = "off" in command.args.lower()
    if message.chat.id not in group_settings: group_settings[message.chat.id] = {}
    group_settings[message.chat.id]["sticker_block"] = status
    await message.answer(f"🚫 Stiker bloku: {'Aktiv' if status else 'Deaktiv'}")

# --- ÜMUMİ FİLTR (SÖYÜŞ, LİNK, STİKER SİLMƏ) ---
@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def main_filter(message: types.Message):
    # Link silmə
    if message.text and ("t.me/" in message.text or "http" in message.text):
        if not await is_user_admin(message.chat.id, message.from_user.id):
            await message.delete()
            return

    # Söyüş silmə
    if message.text and any(word in message.text.lower() for word in BAD_WORDS):
        await message.delete()
        return

    # Stiker silmə (Əgər blok aktivdirsə)
    if message.sticker or message.animation:
        if group_settings.get(message.chat.id, {}).get("sticker_block", False):
            await message.delete()

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
