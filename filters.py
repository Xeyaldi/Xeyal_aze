from aiogram import types, Bot
from aiogram.types import Message

# Söyüş siyahısı
BAD_WORDS = ["söyüş1", "söyüş2", "gic", "fahişə", "qəhbə", "bic", "peysər", "sik", "amcıq"]

async def global_cleaner(message: Message, group_settings: dict, is_admin_func, OWNER_ID: int):
    if not message.chat or message.chat.type == "private":
        return

    chat_id = message.chat.id
    user_id = message.from_user.id

    # Admin və ya Sahibdirsə heç nəyi silmə
    if user_id == OWNER_ID or await is_admin_func(chat_id, user_id):
        return

    # 1. Stiker, Gif və Yumru Video bloku
    if group_settings.get(chat_id, {}).get("sticker_block", False):
        if message.sticker or message.animation or message.video_note:
            try:
                await message.delete()
                return
            except:
                pass

    # 2. Söyüş bloku
    if message.text:
        if any(word in message.text.lower() for word in BAD_WORDS):
            try:
                await message.delete()
                return
            except:
                pass
