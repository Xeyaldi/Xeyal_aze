import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

API_TOKEN = 'BOT_TOKEN_BURAYA'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Ayarları yadda saxlamaq üçün (Sadəlik üçün RAM-da tutulur)
# Real layihədə verilənlər bazası (Database) istifadə edilməlidir
group_settings = {} # {chat_id: {"sticker_block": True}}

# Söyüş siyahısı (Bura istədiyin sözləri əlavə edə bilərsən)
BAD_WORDS = ["söyüş1", "söyüş2", "təhqir1"]

# Start Mesajı və Düymələr
@dp.message(Command("start"))
async def start_command(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Məni Qrupa Əlavə Et ➕", url=f"https://t.me/{(await bot.get_me()).username}?startgroup=true"))
    builder.row(
        types.InlineKeyboardButton(text="Kanalımız 📢", url="https://t.me/ht_bots"),
        types.InlineKeyboardButton(text="Dəstək Qrupu 👥", url="https://t.me/ht_bots_chat")
    )
    
    text = (
        "👋 Salam! Mən qrupları qoruyan köməkçi botam.\n\n"
        "🛡 **Funksiyalarım:**\n"
        "• Stiker və GIF-lərin idarə olunması\n"
        "• Anti-söyüş sistemi\n"
        "• Premium emojilərin silinməsi\n\n"
        "👤 **Sahibim:** @kullaniciadidi\n"
        "⚙️ **Əmrlər:** /stiker off və /stiker on"
    )
    await message.answer(text, reply_markup=builder.as_markup())

# Stiker tənzimləmə əmri
@dp.message(Command("stiker"))
async def set_sticker_mode(message: types.Message):
    # Yalnız adminlərin icazəsi olsun (İstəsəniz bu yoxlamanı yığışdıra bilərsiz)
    args = message.text.split()
    if len(args) < 2:
        return await message.answer("İstifadə: `/stiker off` və ya `/stiker on`")
    
    status = args[1].lower()
    if status == "off":
        group_settings[message.chat.id] = {"sticker_block": True}
        await message.answer("🚫 Bu qrupda stiker və GIF-lər **qadağan edildi**.")
    elif status == "on":
        group_settings[message.chat.id] = {"sticker_block": False}
        await message.answer("✅ Bu qrupda stiker və GIF-lər **aktiv edildi**.")

# Mesajları izləyən funksiya
@dp.message()
async def monitor_messages(message: types.Message):
    chat_id = message.chat.id
    
    # 1. Anti-Stiker / GIF / Premium Emoji Yoxlaması
    is_blocked = group_settings.get(chat_id, {}).get("sticker_block", False)
    if is_blocked:
        if message.sticker or message.animation or message.premium_animation:
            try:
                await message.delete()
                return # Mesaj silindisə söyüş yoxlamasına ehtiyac qalmır
            except:
                pass

    # 2. Anti-Söyüş Yoxlaması
    if message.text:
        msg_text = message.text.lower()
        for word in BAD_WORDS:
            if word in msg_text:
                try:
                    await message.delete()
                    # Könüllü: İstifadəçiyə xəbərdarlıq
                    # await message.answer(f"@{message.from_user.username}, söyüş söymək olmaz!")
                    break
                except:
                    pass

async def main():
    print("Bot aktivdir...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
