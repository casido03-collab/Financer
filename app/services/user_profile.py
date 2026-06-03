from app.database import db
from app.services.finance_calculators import calculate_financial_score


async def build_profile_text(user: dict) -> str:
    profile = await db.get_user_profile(user["id"])
    if not profile:
        return "Профиль не заполнен. Пройдите диагностику командой /start."

    score = profile.get("financial_score", 0)
    main_risk = profile.get("main_risk", "Не определен")

    lines = [
        "📊 <b>Ваш финансовый профиль</b>\n",
        f"👔 Занятость: {profile.get('work_type', '—')}",
        f"🏭 Сфера: {profile.get('work_sphere', '—')}",
        f"💰 Доход: {profile.get('income_range', '—')}",
        f"💸 Стиль трат: {profile.get('spending_style', '—')}",
        f"📚 Фин. грамотность: {profile.get('financial_literacy', '—')}",
        f"🛒 Импульсивные покупки: {profile.get('impulsive_spending', '—')}",
        f"📋 Учет расходов: {profile.get('expense_tracking', '—')}",
        f"💳 Долги: {profile.get('debts_status', '—')}",
        f"📅 Перед зарплатой: {profile.get('salary_end_status', '—')}",
        f"💵 Остаток: {profile.get('money_before_salary', '—')}",
        f"\n📈 <b>Финансовый рейтинг: {score}/100</b>",
        f"⚠️ Основной риск: {main_risk}",
    ]
    return "\n".join(lines)


async def recalculate_score(user_id: int):
    profile = await db.get_user_profile(user_id)
    if not profile:
        return
    score, main_risk = calculate_financial_score(profile)
    await db.save_user_profile(user_id, {"financial_score": score, "main_risk": main_risk})
