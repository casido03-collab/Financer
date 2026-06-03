from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from app.database import db
from app.keyboards.reply import back_to_menu_kb

router = Router()


@router.message(F.text == "📈 Финансовый рейтинг")
async def financial_rating(message: Message, state: FSMContext):
    await state.clear()
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Сначала запустите бота командой /start")
        return

    profile = await db.get_user_profile(user["id"])
    if not profile:
        await message.answer(
            "Для расчёта рейтинга нужно пройти диагностику.\nЗапустите /start",
            reply_markup=back_to_menu_kb(),
        )
        return

    score = profile.get("financial_score", 0)
    main_risk = profile.get("main_risk", "Не определен")

    spending = profile.get("spending_style", "")
    tracking = profile.get("expense_tracking", "")
    impulsive = profile.get("impulsive_spending", "")
    debts = profile.get("debts_status", "")
    salary_end = profile.get("salary_end_status", "")

    control_level = _get_level(spending, {
        "Трачу с умом": "высокий",
        "Иногда трачу лишнее": "средний",
        "Часто покупаю ненужное": "низкий",
        "Почти не контролирую расходы": "очень низкий",
    })

    debt_risk = _get_level(debts, {
        "Нет": "низкий",
        "Есть кредитка": "средний",
        "Есть кредит": "высокий",
        "Есть рассрочка": "средний",
        "Есть несколько долгов": "очень высокий",
    })

    stability = "сильная" if score >= 70 else ("умеренная" if score >= 50 else ("слабая" if score >= 30 else "критическая"))

    growth_zone = _get_growth_zone(score, profile)

    text = (
        f"📈 <b>Ваш финансовый рейтинг: {score}/100</b>\n\n"
        f"Контроль расходов: {control_level}\n"
        f"Риск долгов: {debt_risk}\n"
        f"Финансовая устойчивость: {stability}\n\n"
        f"⚠️ Основной риск: {main_risk}\n\n"
        f"🎯 Главная зона роста:\n{growth_zone}"
    )

    await message.answer(text, reply_markup=back_to_menu_kb(), parse_mode="HTML")


def _get_level(value: str, mapping: dict) -> str:
    return mapping.get(value, "не определён")


def _get_growth_zone(score: int, profile: dict) -> str:
    if score < 30:
        return "Начните с составления бюджета хотя бы на 5 дней. Это сразу снизит стресс от нехватки денег."
    elif score < 50:
        return "Начните планировать расходы хотя бы на 5 дней вперёд. Это ключевой шаг к финансовой стабильности."
    elif score < 70:
        if profile.get("expense_tracking") in ("Нет", "Пробовал, но бросил"):
            return "Начните вести учёт расходов хотя бы раз в неделю. Знание — это контроль."
        return "Сосредоточьтесь на снижении импульсивных покупок и создании финансовой подушки."
    elif score < 85:
        return "Вы на хорошем уровне! Следующий шаг — создать резервный фонд на 3 месяца расходов."
    else:
        return "Отличный результат! Рассмотрите возможность формирования долгосрочных накоплений."
