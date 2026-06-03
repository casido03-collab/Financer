from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def upsell_14_days_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⭐ Получить план на 14 дней", callback_data="buy_14_days")
    return builder.as_markup()


def articles_list_kb(page: int = 0) -> InlineKeyboardMarkup:
    from app.texts.articles import ARTICLES
    builder = InlineKeyboardBuilder()
    items = list(ARTICLES.items())
    per_page = 5
    start = page * per_page
    end = start + per_page

    for article_id, article in items[start:end]:
        builder.button(
            text=f"{article_id}. {article['title']}",
            callback_data=f"article_{article_id}"
        )

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"articles_page_{page - 1}"))
    if end < len(items):
        nav_buttons.append(InlineKeyboardButton(text="▶️ Далее", callback_data=f"articles_page_{page + 1}"))

    builder.adjust(1)
    if nav_buttons:
        builder.row(*nav_buttons)

    return builder.as_markup()


def back_to_articles_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ К списку статей", callback_data="articles_page_0")
    return builder.as_markup()


def subscription_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⭐ Купить план на 14 дней — 200 ⭐", callback_data="buy_14_days")
    builder.adjust(1)
    return builder.as_markup()


def confirm_goal_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Сохранить цель", callback_data="goal_confirm")
    builder.button(text="✏️ Изменить", callback_data="goal_edit")
    builder.adjust(2)
    return builder.as_markup()


def credit_cards_list_kb(cards: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for card in cards:
        builder.button(
            text=f"💳 {card['card_name']} — {card['debt_amount']:,.0f} ₽",
            callback_data=f"card_view_{card['id']}"
        )
    builder.button(text="➕ Добавить карту", callback_data="card_add")
    builder.adjust(1)
    return builder.as_markup()


def card_actions_kb(card_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🗑️ Удалить", callback_data=f"card_delete_{card_id}")
    builder.button(text="◀️ Назад", callback_data="cards_back")
    builder.adjust(2)
    return builder.as_markup()
