import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- KONFİQURASİYA ---
OWNER_ID = 8024893255 
API_TOKEN = os.getenv("BOT_TOKEN") 

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Professional Yaddaş Sistemi (RAM)
fed_db = {}           
group_feds = {}       
group_settings = {}   
BAD_WORDS = ["söyüş1", "söyüş2"] 

# --- KÖMƏKÇİ FUNKSİYALAR ---
async def is_user_admin(chat_id: int, user_id: int):
    if user_id == OWNER_ID: return True
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ["administrator", "creator"]
    except: return False

# --- ŞƏXSİ MESAJDA QRUP ƏMRLƏRİNƏ QADAĞA ---
# Bu siyahıdakı əmrlər özəldə yazılanda bot xəbərdarlıq edəcək
GROUP_ONLY_COMMANDS = ["ban", "unban", "gfban", "ungfban", "admin", "unadmin", "stiker", "setwelcome", "joinfed", "gfedpromote", "gfeddemote"]

@dp.message(Command(*GROUP_ONLY_COMMANDS))
async def restrict_private_commands(message: types.Message):
    if message.chat.type == "private":
        await message.answer("⚠️ Bu əmr yalnız qruplarda istifadə edilə bilər!")
        return

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
        "Mən qrupların təhlükəsizliyini təmin etmək, stikerləri və söyüşləri təmizləmək, "
        "federasiya banlarını idarə etmək üçün yaradılmışam.\n\n"
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
        "/gfban - Qlobal ban (Reply)\n"
        "/ungfban - Qlobal banı açır\n"
        "/gfedpromote - Fed admini edir\n\n"
        "⚙️ Qrup İdarəetmə:\n"
        "/ban - İstifadəçini qovur (Reply)\n"
        "/unban - Banı açır (Reply)\n"
        "/admin [yetgi] - Admin edir (Reply)\n"
        "/unadmin - Adminliyi alır\n"
        "/stiker off/on - Stikerləri bağlayır/açır\n"
        "/setwelcome [mətn] - Qarşılama mesajı"
    )
    await message.answer(help_text)

# --- BAN & UNBAN ---

@dp.message(Command("ban"))
async def cmd_ban(message: types.Message):
    if message.chat.type == "private": return # Yuxarıdakı filtr artıq xəbərdarlıq edir
    if not await is_user_admin(message.chat.id, message.from_user.id):
        return await message.answer("❌ Sizin ban etmək icazəniz yoxdur.")
    if not message.reply_to_message:
        return await message.answer("İstifadəçini ban etmək üçün onun mesajını cavablayın (reply).")
    try:
        await bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
        await message.answer(f"🚫 {message.reply_to_message.from_user.first_name} qrupdan qovuldu.")
    except:
        await message.answer("❌ Məni admin edib 'Ban' yetgisi verdiyinizdən əmin olun.")

@dp.message(Command("unban"))
async def cmd_unban(message: types.Message):
    if not await is_user_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    try:
        await bot.unban_chat_member(message.chat.id, message.reply_to_message.from_user.id, only_if_banned=True)
        await message.answer(f"✅ {message.reply_to_message.from_user.first_name} banı açıldı.")
    except: pass

# --- FEDERASİYA (GFBAN) ---

@dp.message(Command("gfban"))
async def cmd_gfban(message: types.Message):
    fed_id = group_feds.get(message.chat.id)
    if not fed_id: return await message.answer("❌ Bu qrup hər hansı bir federasiyaya bağlı deyil.")
    if message.from_user.id != fed_db[fed_id]["owner"] and message.from_user.id not in fed_db[fed_id]["admins"]:
        return await message.answer("❌ Bu yetginiz yoxdur.")
    if not message.reply_to_message: return await message.answer("GFBAN üçün reply edin.")
    
    target_id = message.reply_to_message.from_user.id
    fed_db[fed_id]["banned_users"].add(target_id)
    try:
        await bot.ban_chat_member(message.chat.id, target_id)
        await message.answer(f"🌏 GFBAN! İstifadəçi {fed_db[fed_id]['name']} federasiyasından qovuldu.")
    except: pass

# --- ADMİN VƏ YETGİ ---

@dp.message(Command("admin"))
async def cmd_promote(message: types.Message, command: CommandObject):
    if not await is_user_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    title = command.args if command.args else "Admin"
    try:
        await bot.promote_chat_member(message.chat.id, message.reply_to_message.from_user.id, can_delete_messages=True, can_restrict_members=True, can_invite_users=True, can_pin_messages=True)
        await bot.set_chat_administrator_custom_title(message.chat.id, message.reply_to_message.from_user.id, title)
        await message.answer(f"✅ {message.reply_to_message.from_user.first_name} indi **{title}** rütbəsində admindir!")
    except: pass

# --- QRUPA GİRİŞ/ÇIXIŞ ---

@dp.message(F.new_chat_members)
async def on_join(message: types.Message):
    bot_id = (await bot.get_me()).id
    for user in message.new_chat_members:
        if user.id == bot_id:
            await message.answer("🎉 Məni qrupa əlavə etdiyiniz üçün təşəkkürlər! Qrupu qorumağım üçün məni admin edin.")
        else:
            settings = group_settings.get(message.chat.id, {})
            text = settings.get("welcome", "Xoş gəldin {user}!").replace("{user}", user.first_name)
            await message.answer(text)
            try: await bot.send_message(user.id, f"Salam! {message.chat.title} qrupuna xoş gəldin.")
            except: pass

# --- FİLTRLƏR (STİKER & SÖYÜŞ) ---

@dp.message(F.sticker | F.animation | F.premium_animation)
async def sticker_filter(message: types.Message):
    if group_settings.get(message.chat.id, {}).get("sticker_block", False):
        await message.delete()

@dp.message()
async def main_handler(message: types.Message):
    if message.chat.type == "private": return
    if message.text and any(word in message.text.lower() for word in BAD_WORDS):
        await message.delete()
        return
    if message.text and message.text.startswith("/stiker"):
        if not await is_user_admin(message.chat.id, message.from_user.id): return
        status = "off" in message.text.lower()
        if message.chat.id not in group_settings: group_settings[message.chat.id] = {}
        group_settings[message.chat.id]["sticker_block"] = status
        await message.answer(f"🚫 Stiker bloku: {'Aktiv' if status else 'Deaktiv'}")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
