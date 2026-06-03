from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()


def start_onboarding_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🚀 Начать диагностику")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def work_type_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👨‍💼 Наемный сотрудник"), KeyboardButton(text="🧾 Самозанятый")],
            [KeyboardButton(text="🏢 Предприниматель"), KeyboardButton(text="🎓 Студент")],
            [KeyboardButton(text="👵 Пенсионер"), KeyboardButton(text="🔎 Временно без работы")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def income_range_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="до 30 000 ₽"), KeyboardButton(text="30 000 – 50 000 ₽")],
            [KeyboardButton(text="50 000 – 80 000 ₽"), KeyboardButton(text="80 000 – 120 000 ₽")],
            [KeyboardButton(text="120 000 – 200 000 ₽"), KeyboardButton(text="более 200 000 ₽")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def spending_style_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Трачу с умом")],
            [KeyboardButton(text="Иногда трачу лишнее")],
            [KeyboardButton(text="Часто покупаю ненужное")],
            [KeyboardButton(text="Почти не контролирую расходы")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def financial_literacy_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Да, хорошо разбираюсь")],
            [KeyboardButton(text="Что-то понимаю")],
            [KeyboardButton(text="Почти не разбираюсь")],
            [KeyboardButton(text="Хочу разобраться с нуля")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def impulsive_spending_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Нет, редко"), KeyboardButton(text="Иногда")],
            [KeyboardButton(text="Часто"), KeyboardButton(text="Да, это моя главная проблема")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def expense_tracking_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Да, регулярно"), KeyboardButton(text="Иногда")],
            [KeyboardButton(text="Нет"), KeyboardButton(text="Пробовал, но бросил")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def debts_status_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Нет"), KeyboardButton(text="Есть кредитка")],
            [KeyboardButton(text="Есть кредит"), KeyboardButton(text="Есть рассрочка")],
            [KeyboardButton(text="Есть несколько долгов")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def salary_end_status_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Не остается вообще")],
            [KeyboardButton(text="Остаюсь примерно в ноль")],
            [KeyboardButton(text="Иногда немного остается")],
            [KeyboardButton(text="Удается откладывать")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def money_before_salary_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="0 ₽"), KeyboardButton(text="до 1 000 ₽")],
            [KeyboardButton(text="1 000 – 5 000 ₽"), KeyboardButton(text="5 000 – 10 000 ₽")],
            [KeyboardButton(text="больше 10 000 ₽")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def open_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📋 Открыть главное меню")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💬 Консультация"), KeyboardButton(text="📊 Проверка бюджета")],
            [KeyboardButton(text="💳 Кредитные карты"), KeyboardButton(text="🎯 Моя цель")],
            [KeyboardButton(text="💸 Куда уходят деньги"), KeyboardButton(text="📈 Финансовый рейтинг")],
            [KeyboardButton(text="📚 Полезные статьи"), KeyboardButton(text="👤 Личный кабинет")],
        ],
        resize_keyboard=True,
    )


def back_to_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⬅️ Главное меню")]],
        resize_keyboard=True,
    )


def cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена"), KeyboardButton(text="⬅️ Главное меню")]],
        resize_keyboard=True,
    )


def credit_cards_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🧮 Рассчитать платеж"), KeyboardButton(text="📅 Когда закрою долг")],
            [KeyboardButton(text="💸 Сколько переплачу"), KeyboardButton(text="📋 План выхода из долгов")],
            [KeyboardButton(text="⚠️ Риск кредитки"), KeyboardButton(text="⬅️ Главное меню")],
        ],
        resize_keyboard=True,
    )


def expense_categories_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Еда вне дома"), KeyboardButton(text="Доставка")],
            [KeyboardButton(text="Такси"), KeyboardButton(text="Маркетплейсы")],
            [KeyboardButton(text="Подписки"), KeyboardButton(text="Кредиты")],
            [KeyboardButton(text="Развлечения"), KeyboardButton(text="Другое")],
            [KeyboardButton(text="✅ Готово"), KeyboardButton(text="⬅️ Главное меню")],
        ],
        resize_keyboard=True,
    )


def personal_cabinet_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💎 Подписка"), KeyboardButton(text="📊 Мой финансовый профиль")],
            [KeyboardButton(text="🎯 Моя цель"), KeyboardButton(text="💳 Мои кредитки")],
            [KeyboardButton(text="📜 История консультаций"), KeyboardButton(text="⚙️ Изменить данные")],
            [KeyboardButton(text="⬅️ Главное меню")],
        ],
        resize_keyboard=True,
    )


def goal_actions_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✏️ Изменить цель"), KeyboardButton(text="📊 Проверить прогресс")],
            [KeyboardButton(text="⬅️ Главное меню")],
        ],
        resize_keyboard=True,
    )


def consultation_mode_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Бесплатный план на 5 дней")],
            [KeyboardButton(text="⬅️ Главное меню")],
        ],
        resize_keyboard=True,
    )


def expense_analysis_mode_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Анализ по категориям")],
            [KeyboardButton(text="✍️ Свободный ввод (ИИ-анализ)")],
            [KeyboardButton(text="⬅️ Главное меню")],
        ],
        resize_keyboard=True,
    )
