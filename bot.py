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

# Yaddaş (Database)
fed_db = {}           
group_feds = {}       
group_settings = {}   
BAD_WORDS = ["söyüş1", "söyüş2"] 

# --- KÖMƏKÇİ FUNKSİYA: Admin Yoxlaması ---
async def is_admin(chat_id, user_id):
    if user_id == OWNER_ID: return True
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ["administrator", "creator"]
    except: return False

# --- START VƏ BUTONLAR ---
@dp.message(Command("start"))
async def start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Məni Qrupa Əlavə Et ➕", url=f"https://t.me/{(await bot.get_me()).username}?startgroup=true"))
    builder.row(
        types.InlineKeyboardButton(text="Kanal 📢", url="https://t.me/ht_bots"),
        types.InlineKeyboardButton(text="Dəstək 👥", url="https://t.me/ht_bots_chat")
    )
    builder.row(types.InlineKeyboardButton(text="👨‍💻 Developer", url="https://t.me/kullaniciadidi"))
    
    await message.answer(
        f"🤖 **HT-Security Premium Bot**\n\n"
        f"👤 **Sahib:** @kullaniciadidi\n"
        f"🛠 **Status:** Aktiv\n\n"
        "Bütün əmrləri görmək üçün `/help` yazın.",
        reply_markup=builder.as_markup()
    )

# --- HELP MENYUSU ---
@dp.message(Command("help"))
async def help_command(message: types.Message):
    help_text = (
        "📜 **Botun Əmrləri:**\n\n"
        "🛡 **Federasiya:**\n"
        "• `/newfed [ad]` - Yeni Fed yaradır\n"
        "• `/joinfed [id]` - Qrupu Fed-ə bağlayır\n"
        "• `/gfban` - Fed səviyyəsində ban (Reply)\n"
        "• `/ungfban` - Fed banını açır\n"
        "• `/gfedpromote` - Fed admini təyin edir\n\n"
        "⚙️ **Qrup İdarəetmə:**\n"
        "• `/admin [yetgi]` - Admin təyin edir (Reply)\n"
        "• `/unadmin` - Adminliyi alır\n"
        "• `/stiker off/on` - Stikerləri bağlayır/açır\n"
        "• `/setwelcome [mətn]` - Qarşılama mesajı\n"
    )
    await message.answer(help_text)

# --- QRUPA ƏLAVƏ EDİLDİKDƏ TƏŞƏKKÜR ---
@dp.message(F.new_chat_members)
async def on_bot_join(message: types.Message):
    bot_obj = await bot.get_me()
    for user in message.new_chat_members:
        if user.id == bot_obj.id:
            await message.answer("🎉 Məni qrupa əlavə etdiyiniz üçün təşəkkürlər! Qrupun tam təhlükəsizliyi artıq mənim əlimdədir. Zəhmət olmasa məni admin edin.")

# --- BAN SİSTEMİ (DÜZƏLDİLMİŞ) ---
@dp.message(Command("gfban"))
async def gfban(message: types.Message):
    if not message.reply_to_message:
        return await message.answer("Ban etmək üçün istifadəçini reply edin.")
    
    fed_id = group_feds.get(message.chat.id)
    if not fed_id:
        return await message.answer("❌ Bu qrup hər hansı bir federasiyaya bağlı deyil.")

    user_id = message.from_user.id
    if user_id != fed_db[fed_id]["owner"] and user_id not in fed_db[fed_id]["admins"]:
        return await message.answer("❌ Sizin buna yetginiz yoxdur.")

    target_id = message.reply_to_message.from_user.id
    fed_db[fed_id]["banned_users"].add(target_id)
    
    try:
        await bot.ban_chat_member(message.chat.id, target_id)
        await message.answer(f"🌏 **GFBAN edildi!**\nFederasiya: {fed_db[fed_id]['name']}")
    except:
        await message.answer("❌ Xəta! Bot admin olmalıdır.")

# --- DİGƏR FUNKSİYALAR (Admin, Unadmin, Stiker) ---
@dp.message(Command("admin"))
async def promote(message: types.Message, command: CommandObject):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    title = command.args or "Admin"
    user_id = message.reply_to_message.from_user.id
    try:
        await bot.promote_chat_member(message.chat.id, user_id, can_delete_messages=True, can_restrict_members=True, can_pin_messages=True)
        await bot.set_chat_administrator_custom_title(message.chat.id, user_id, title)
        await message.answer(f"✅ {message.reply_to_message.from_user.first_name} indi **{title}** rütbəsində admindir!")
    except: await message.answer("❌ Botda admin təyin etmək hüququ yoxdur.")

@dp.message(Command("stiker"))
async def st_toggle(message: types.Message, command: CommandObject):
    if not await is_admin(message.chat.id, message.from_user.id): return
    status = (command.args.lower() == "off") if command.args else False
    if message.chat.id not in group_settings: group_settings[message.chat.id] = {}
    group_settings[message.chat.id]["sticker_block"] = status
    await message.answer(f"🚫 Stiker bloku: {'Aktiv' if status else 'Deaktiv'}")

@dp.message()
async def filter_messages(message: types.Message):
    # Stiker silmə
    if group_settings.get(message.chat.id, {}).get("sticker_block", False):
        if message.sticker or message.animation or message.premium_animation:
            await message.delete()
            return
    # Söyüş silmə
    if message.text and any(word in message.text.lower() for word in BAD_WORDS):
        await message.delete()

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
