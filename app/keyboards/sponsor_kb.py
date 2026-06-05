from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def sponsor_gate_kb(subscribe_url: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ Подписаться", url=subscribe_url)
    b.button(text="🔄 Проверить подписку", callback_data="sponsor:check")
    b.adjust(1)
    return b.as_markup()
