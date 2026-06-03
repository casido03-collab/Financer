from collections import defaultdict
from time import monotonic
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

# ─── Лимиты (секунды) ────────────────────────────────────────────────────────
MESSAGE_COOLDOWN   = 0.7   # обычные сообщения / нажатия кнопок reply
CALLBACK_COOLDOWN  = 1.0   # инлайн-кнопки
AI_COOLDOWN        = 25.0  # запросы к OpenAI (консультация, анализ расходов)

# Хендлеры, которые дёргают OpenAI — применяется AI_COOLDOWN
AI_HANDLERS = {
    "consultation_income",       # начало консультации
    "expenses_free_text_handler",# анализ расходов через ИИ
    "consultation_mandatory",    # финальный шаг → генерация плана
    "debt_plan_start",           # план выхода из долгов
}

# Сколько подряд проигнорированных запросов до предупреждения
WARN_AFTER = 3
# ─────────────────────────────────────────────────────────────────────────────


class MessageThrottlingMiddleware(BaseMiddleware):
    def __init__(self):
        self._last: Dict[int, float] = defaultdict(float)
        self._ai_last: Dict[int, float] = defaultdict(float)
        self._strikes: Dict[int, int] = defaultdict(int)

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id if event.from_user else None
        if user_id is None:
            return await handler(event, data)

        now = monotonic()
        elapsed = now - self._last[user_id]

        if elapsed < MESSAGE_COOLDOWN:
            self._strikes[user_id] += 1
            if self._strikes[user_id] == WARN_AFTER:
                await event.answer(
                    "⏳ Не так быстро — подождите секунду между запросами."
                )
            return  # молча игнорируем

        self._strikes[user_id] = 0
        self._last[user_id] = now

        # Проверяем AI-лимит для тяжёлых хендлеров
        handler_name = handler.__name__ if hasattr(handler, "__name__") else ""
        if handler_name in AI_HANDLERS:
            ai_elapsed = now - self._ai_last[user_id]
            if ai_elapsed < AI_COOLDOWN:
                remaining = int(AI_COOLDOWN - ai_elapsed)
                await event.answer(
                    f"⏳ Следующий запрос к ИИ доступен через {remaining} сек."
                )
                return
            self._ai_last[user_id] = now

        return await handler(event, data)


class CallbackThrottlingMiddleware(BaseMiddleware):
    def __init__(self):
        self._last: Dict[int, float] = defaultdict(float)
        self._strikes: Dict[int, int] = defaultdict(int)

    async def __call__(
        self,
        handler: Callable[[CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id if event.from_user else None
        if user_id is None:
            return await handler(event, data)

        now = monotonic()
        elapsed = now - self._last[user_id]

        if elapsed < CALLBACK_COOLDOWN:
            self._strikes[user_id] += 1
            if self._strikes[user_id] == WARN_AFTER:
                await event.answer("⏳ Не так быстро!", show_alert=False)
            else:
                await event.answer()  # убираем часики на кнопке без текста
            return

        self._strikes[user_id] = 0
        self._last[user_id] = now
        return await handler(event, data)
