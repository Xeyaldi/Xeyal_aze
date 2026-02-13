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

# Yaddaş sistemi (RAM)
fed_db = {}           
group_feds = {}       
group_settings = {}   
BAD_WORDS = ["söyüş1", "söyüş2"] 

# --- KÖMƏKÇİ FUNKSİYA ---
async def is_admin(chat_id, user_id):
    if user_id == OWNER_ID: return True
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ["administrator", "creator"]
    except: return False

# --- START MESAJI ---
@dp.message(Command("start"))
async def start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Məni Qrupa Əlavə Et ➕", url=f"https://t.me/{(await bot.get_me()).username}?startgroup=true"))
    builder.row(
        types.InlineKeyboardButton(text="Kanal 📢", url="https://t.me/ht_bots"),
        types.InlineKeyboardButton(text="Dəstək 👥", url="https://t.me/ht_bots_chat")
    )
    builder.row(types.InlineKeyboardButton(text="👨‍💻 Developer", url="https://t.me/kullaniciadidi"))
    
    text = (
        "🤖 Flower-Security Premium Bot\n\n"
        "Mən qrupların təhlükəsizliyini təmin etmək,qrup idarəsində kömək üçün botam , "
        "qrupunuza məni əlavə edərək istifadə edə bilərsiniz.\n\n"
        "Kömək üçün /help yazın."
    )
    await message.answer(text, reply_markup=builder.as_markup())

# --- BAN VƏ UNBAN ƏMRLƏRİ ---

@dp.message(Command("ban"))
async def simple_ban(message: types.Message):
    if message.chat.type == "private":
        return await message.answer("⚠️ Bu əmr yalnız qruplarda işləyir!")
    
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.answer("❌ Sizin ban etmək yetginiz yoxdur.")

    if not message.reply_to_message:
        return await message.answer("Ban etmək üçün istifadəçini reply edin.")

    try:
        await bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
        await message.answer(f"🚫 {message.reply_to_message.from_user.first_name} qrupdan ban olundu.")
    except:
        await message.answer("❌ Xəta! Botun admin hüququnu yoxlayın.")

@dp.message(Command("unban"))
async def simple_unban(message: types.Message):
    if message.chat.type == "private":
        return await message.answer("⚠️ Bu əmr yalnız qruplarda işləyir!")

    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.answer("❌ Sizin yetginiz yoxdur.")

    if not message.reply_to_message:
        return await message.answer("Banı açmaq üçün istifadəçini reply edin.")

    try:
        await bot.unban_chat_member(message.chat.id, message.reply_to_message.from_user.id, only_if_banned=True)
        await message.answer(f"✅ {message.reply_to_message.from_user.first_name} banı açıldı.")
    except:
        await message.answer("❌ Xəta baş verdi.")

# --- FEDERASİYA BANLARI (GFBAN) ---

@dp.message(Command("gfban"))
async def global_ban(message: types.Message):
    if message.chat.type == "private":
        return await message.answer("⚠️ Bu əmr yalnız qruplarda işləyir!")

    fed_id = group_feds.get(message.chat.id)
    if not fed_id:
        return await message.answer("❌ Bu qrup federasiyaya qoşulmayıb.")

    if message.from_user.id != fed_db[fed_id]["owner"] and message.from_user.id not in fed_db[fed_id]["admins"]:
        return await message.answer("❌ Federasiya yetginiz yoxdur.")

    if not message.reply_to_message:
        return await message.answer("GFBAN üçün reply edin.")

    target_id = message.reply_to_message.from_user.id
    fed_db[fed_id]["banned_users"].add(target_id)
    
    try:
        await bot.ban_chat_member(message.chat.id, target_id)
        await message.answer(f"🌏 GFBAN! İstifadəçi {fed_db[fed_id]['name']} federasiyasından qovuldu.")
    except:
        pass

# --- DİGƏR FİLTRLƏR (STİKER, SÖYÜŞ) ---
@dp.message()
async def filter_handler(message: types.Message):
    if message.chat.type == "private": return
    
    # Stiker bloku
    if group_settings.get(message.chat.id, {}).get("sticker_block", False):
        if message.sticker or message.animation or message.premium_animation:
            await message.delete()
            return

    # Söyüş bloku
    if message.text and any(word in message.text.lower() for word in BAD_WORDS):
        await message.delete()

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
