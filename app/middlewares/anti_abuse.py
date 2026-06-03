from collections import defaultdict
from time import monotonic
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

# ─── Лимиты ──────────────────────────────────────────────────────────────────
MESSAGE_COOLDOWN  = 0.3   # сообщения / reply-кнопки (0.3с = защита от ботов, не мешает людям)
CALLBACK_COOLDOWN = 1.0   # инлайн-кнопки
AI_COOLDOWN       = 25.0  # запросы к OpenAI
WARN_AFTER        = 4     # предупреждение после N подряд заблокированных запросов
# ─────────────────────────────────────────────────────────────────────────────

# AI-хендлеры отслеживаются отдельно через декоратор ai_throttle (см. ниже)
_ai_last: Dict[int, float] = defaultdict(float)


def ai_throttle(handler):
    """Декоратор для хендлеров которые дёргают OpenAI."""
    async def wrapper(message: Message, **kwargs):
        user_id = message.from_user.id
        elapsed = monotonic() - _ai_last[user_id]
        if elapsed < AI_COOLDOWN:
            remaining = int(AI_COOLDOWN - elapsed)
            await message.answer(
                f"⏳ Следующий запрос к ИИ доступен через {remaining} сек."
            )
            return
        _ai_last[user_id] = monotonic()
        return await handler(message, **kwargs)
    wrapper.__name__ = handler.__name__
    return wrapper


class MessageThrottlingMiddleware(BaseMiddleware):
    def __init__(self):
        self._last:   Dict[int, float] = defaultdict(float)
        self._strikes: Dict[int, int]  = defaultdict(int)

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id if event.from_user else None
        if user_id is None:
            return await handler(event, data)

        now     = monotonic()
        elapsed = now - self._last[user_id]

        if elapsed < MESSAGE_COOLDOWN:
            self._strikes[user_id] += 1
            if self._strikes[user_id] == WARN_AFTER:
                await event.answer("⏳ Не так быстро — сделайте паузу.")
            return  # молча игнорируем

        self._strikes[user_id] = 0
        self._last[user_id] = now
        return await handler(event, data)


class CallbackThrottlingMiddleware(BaseMiddleware):
    def __init__(self):
        self._last:    Dict[int, float] = defaultdict(float)
        self._strikes: Dict[int, int]   = defaultdict(int)

    async def __call__(
        self,
        handler: Callable[[CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id if event.from_user else None
        if user_id is None:
            return await handler(event, data)

        now     = monotonic()
        elapsed = now - self._last[user_id]

        if elapsed < CALLBACK_COOLDOWN:
            self._strikes[user_id] += 1
            if self._strikes[user_id] == WARN_AFTER:
                await event.answer("⏳ Не так быстро!", show_alert=False)
            else:
                await event.answer()
            return

        self._strikes[user_id] = 0
        self._last[user_id] = now
        return await handler(event, data)
