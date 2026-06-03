import asyncio
from aiogram import Bot
from aiogram.methods import SendMessage, SendChatAction
from aiogram.enums import ChatAction


def _pause(text: str) -> float:
    """Typing pause proportional to message length."""
    return min(0.5 + len(text) * 0.03, 2.5)


class TypingBot(Bot):
    """Automatically shows 'typing...' before every outgoing text message."""

    async def __call__(self, method, *args, **kwargs):
        if isinstance(method, SendMessage) and method.text:
            try:
                await super().__call__(
                    SendChatAction(chat_id=method.chat_id, action=ChatAction.TYPING)
                )
                await asyncio.sleep(_pause(method.text))
            except Exception:
                pass
        return await super().__call__(method, *args, **kwargs)
