import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- MƏLUMATLARIN ---
# API ID: 34628590 | API Hash: 78a65ef180771575a50fcd350f027e9d
OWNER_ID = 8024893255 
# Tokeni Heroku-da 'BOT_TOKEN' adı ilə Config Var olaraq əlavə edəcəksən
API_TOKEN = os.getenv("BOT_TOKEN") 

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Yaddaş sistemi
fed_db = {}
group_feds = {}
group_settings = {}
BAD_WORDS = ["söyüş1", "söyüş2"] # Bura qadağan sözləri özün artırarsan

async def is_admin(chat_id, user_id):
    if user_id == OWNER_ID: return True
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ["administrator", "creator"]
    except: return False

# --- ƏMRLƏR ---

@dp.message(Command("start"))
async def start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Məni Qrupa Əlavə Et ➕", url=f"https://t.me/{(await bot.get_me()).username}?startgroup=true"))
    builder.row(
        types.InlineKeyboardButton(text="Kanal 📢", url="https://t.me/ht_bots"),
        types.InlineKeyboardButton(text="Dəstək 👥", url="https://t.me/ht_bots_chat")
    )
    await message.answer(
        f"🤖 **HT-Security Premium Bot**\n\n👤 **Sahib:** @kullaniciadidi\n🛠 **Status:** Aktiv\n\nQrupda kömək üçün `/help` yazın.",
        reply_markup=builder.as_markup()
    )

@dp.message(Command("admin"))
async def promote_admin(message: types.Message, command: CommandObject):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    title = command.args if command.args else "Admin"
    user = message.reply_to_message.from_user
    try:
        await bot.promote_chat_member(message.chat.id, user.id, can_delete_messages=True, can_restrict_members=True)
        await bot.set_chat_administrator_custom_title(message.chat.id, user.id, title)
        await message.answer(f"✅ {user.first_name} indi **{title}**!")
    except: await message.answer("❌ Botda admin təyin etmək hüququ yoxdur.")

@dp.message(Command("unadmin"))
async def demote_admin(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return
    try:
        await bot.promote_chat_member(message.chat.id, message.reply_to_message.from_user.id, is_anonymous=False)
        await message.answer("🗑 Adminlikdən çıxarıldı.")
    except: pass

@dp.message(Command("newfed"))
async def new_fed(message: types.Message, command: CommandObject):
    if not command.args: return
    fed_id = str(abs(hash(command.args)) % 100000)
    fed_db[fed_id] = {"name": command.args, "owner": message.from_user.id, "admins": set(), "banned_users": set()}
    await message.answer(f"✅ Fed Yaradıldı! ID: `{fed_id}`")

@dp.message(Command("joinfed"))
async def join_fed(message: types.Message, command: CommandObject):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if command.args in fed_db:
        group_feds[message.chat.id] = command.args
        await message.answer(f"🔗 Qoşuldu: **{fed_db[command.args]['name']}**")

@dp.message(Command("gfban"))
async def gfban(message: types.Message):
    fed_id = group_feds.get(message.chat.id)
    if not fed_id: return
    if message.from_user.id != fed_db[fed_id]["owner"] and message.from_user.id not in fed_db[fed_id]["admins"]: return
    user_id = message.reply_to_message.from_user.id
    fed_db[fed_id]["banned_users"].add(user_id)
    await bot.ban_chat_member(message.chat.id, user_id)
    await message.answer("🌏 **GFBAN edildi!**")

@dp.message(Command("setwelcome"))
async def set_welcome(message: types.Message, command: CommandObject):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if message.chat.id not in group_settings: group_settings[message.chat.id] = {}
    group_settings[message.chat.id]["welcome"] = command.args
    await message.answer("✅ Qarşılama mesajı yeniləndi.")

@dp.message(Command("stiker"))
async def st_toggle(message: types.Message, command: CommandObject):
    if not await is_admin(message.chat.id, message.from_user.id): return
    status = (command.args.lower() == "off") if command.args else False
    if message.chat.id not in group_settings: group_settings[message.chat.id] = {}
    group_settings[message.chat.id]["sticker_block"] = status
    await message.answer(f"🚫 Stiker bloku: {'Aktiv' if status else 'Deaktiv'}")

@dp.message(F.new_chat_members)
async def on_join(message: types.Message):
    fed_id = group_feds.get(message.chat.id)
    for user in message.new_chat_members:
        if fed_id and user.id in fed_db[fed_id]["banned_users"]:
            await bot.ban_chat_member(message.chat.id, user.id)
            continue
        st = group_settings.get(message.chat.id, {})
        txt = st.get("welcome", "Xoş gəldin {user}!").replace("{user}", user.first_name)
        await message.answer(txt)
        try: await bot.send_message(user.id, f"Xoş gəldin! {message.chat.title} qrupuna qoşuldun.")
        except: pass

@dp.message()
async def filter_all(message: types.Message):
    if message.text and any(word in message.text.lower() for word in BAD_WORDS):
        await message.delete()
        return
    if group_settings.get(message.chat.id, {}).get("sticker_block", False):
        if message.sticker or message.animation or message.premium_animation:
            await message.delete()

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
