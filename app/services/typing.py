import asyncio
from aiogram.types import Message
from aiogram.enums import ChatAction


async def typing(message: Message, seconds: float = 1.5):
    await message.bot.send_chat_action(
        chat_id=message.chat.id,
        action=ChatAction.TYPING,
    )
    await asyncio.sleep(seconds)
