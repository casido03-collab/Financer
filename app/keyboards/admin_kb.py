from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


def admin_main_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="👥 Пользователи",     callback_data="adm_users")
    b.button(text="📊 Retention",        callback_data="adm_retention")
    b.button(text="🚀 Воронка",          callback_data="adm_onboarding")
    b.button(text="📱 Разделы",          callback_data="adm_sections")
    b.button(text="💰 Продажи",          callback_data="adm_sales")
    b.button(text="💵 Доход",            callback_data="adm_revenue")
    b.button(text="🤖 OpenAI",           callback_data="adm_ai")
    b.button(text="📨 Пуши",             callback_data="adm_push")
    b.button(text="📚 Статьи",           callback_data="adm_articles")
    b.button(text="👥 Аудитория",        callback_data="adm_audience")
    b.button(text="🚀 Health Report",    callback_data="adm_health")
    b.adjust(2)
    return b.as_markup()


def admin_back_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="◀️ Назад", callback_data="adm_main")
    return b.as_markup()
