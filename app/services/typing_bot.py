import asyncio
from typing import Any
from aiogram import Bot
from aiogram.enums import ChatAction


def _typing_seconds(text: str) -> float:
    """Calculates typing pause proportional to text length."""
    if not text:
        return 0.5
    return min(0.5 + len(text) * 0.03, 2.5)


class TypingBot(Bot):
    """Bot that shows a 'typing...' indicator before every send_message."""

    async def send_message(self, chat_id: Any, text: str, **kwargs) -> Any:
        pause = _typing_seconds(text)
        try:
            await self.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
            await asyncio.sleep(pause)
        except Exception:
            pass
        return await super().send_message(chat_id=chat_id, text=text, **kwargs)
