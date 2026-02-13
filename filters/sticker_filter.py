from aiogram import types

BAD_WORDS = ["söyüş1", "söyüş2", "gic", "fahişə", "qəhbə", "bic", "peysər", "sik", "amcıq"]

async def global_filter(message: types.Message, bot, is_admin, group_settings):
    if message.chat.type == "private":
        return

    chat_id = message.chat.id

    if not await is_admin(chat_id, message.from_user.id):

        # STIKER / GIF / VIDEO NOTE
        if group_settings.get(chat_id, {}).get("sticker_block", False):
            if message.sticker or message.animation or message.video_note:
                try:
                    await message.delete()
                    return
                except:
                    pass

        # SÖYÜŞ
        if message.text:
            if any(word in message.text.lower() for word in BAD_WORDS):
                try:
                    await message.delete()
                except:
                    pass
