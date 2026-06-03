import math


def calculate_daily_limit(amount: float, days: int) -> dict:
    if days <= 0:
        return {"error": "Количество дней должно быть больше 0"}

    daily = amount / days
    if daily < 500:
        risk = "🔴 Критический"
        recommendation = (
            f"Ваш дневной лимит очень мал. Рекомендуем сократить все необязательные расходы "
            f"до минимума и рассмотреть возможность временного займа у близких."
        )
    elif daily < 1000:
        risk = "🟡 Средний"
        recommendation = (
            f"Бюджет ограничен. Исключите развлечения и доставку еды, "
            f"готовьте дома, используйте общественный транспорт."
        )
    else:
        risk = "🟢 Нормальный"
        recommendation = (
            f"Бюджет достаточный. Придерживайтесь дневного лимита "
            f"и постарайтесь немного отложить перед следующей зарплатой."
        )

    return {
        "daily_limit": round(daily, 2),
        "risk": risk,
        "recommendation": recommendation,
    }


def calculate_credit_payment(debt: float, rate: float, monthly_payment: float) -> dict:
    if monthly_payment <= 0:
        return {"error": "Платеж должен быть больше 0"}

    monthly_rate = rate / 100 / 12
    if monthly_rate == 0:
        if monthly_payment >= debt:
            return {"months": 1, "total_paid": debt, "overpayment": 0}
        months = math.ceil(debt / monthly_payment)
        return {"months": months, "total_paid": monthly_payment * months, "overpayment": 0}

    min_payment = debt * monthly_rate
    if monthly_payment <= min_payment:
        return {
            "error": f"Платеж слишком маленький. Минимум для покрытия процентов: {min_payment:.2f} ₽",
            "warning": True,
        }

    months = math.ceil(
        -math.log(1 - (debt * monthly_rate) / monthly_payment) / math.log(1 + monthly_rate)
    )
    total_paid = monthly_payment * months
    overpayment = total_paid - debt

    warning = ""
    if monthly_payment < debt * monthly_rate * 2:
        warning = "⚠️ Платеж очень маленький — долг будет закрываться очень долго."

    return {
        "months": months,
        "total_paid": round(total_paid, 2),
        "overpayment": round(overpayment, 2),
        "warning": warning,
    }


def calculate_debt_closure(debt: float, monthly_payment: float, rate: float) -> dict:
    monthly_rate = rate / 100 / 12
    if monthly_rate == 0:
        months = math.ceil(debt / monthly_payment) if monthly_payment > 0 else 999
        return {
            "months": months,
            "total_paid": monthly_payment * months,
            "overpayment": 0,
            "recommendation": f"При увеличении платежа на 20% срок закрытия сократится на {int(months * 0.15)} месяцев.",
        }

    min_payment = debt * monthly_rate
    if monthly_payment <= min_payment:
        return {"error": f"Платеж слишком маленький. Минимум: {min_payment:.2f} ₽"}

    months = math.ceil(
        -math.log(1 - (debt * monthly_rate) / monthly_payment) / math.log(1 + monthly_rate)
    )
    total_paid = monthly_payment * months
    overpayment = total_paid - debt

    increased_payment = monthly_payment * 1.2
    months_faster = math.ceil(
        -math.log(1 - (debt * monthly_rate) / increased_payment) / math.log(1 + monthly_rate)
    )

    return {
        "months": months,
        "total_paid": round(total_paid, 2),
        "overpayment": round(overpayment, 2),
        "recommendation": (
            f"Если увеличить платеж до {increased_payment:.0f} ₽/мес, "
            f"долг закроется на {months - months_faster} месяцев быстрее."
        ),
    }


def calculate_overpayment(debt: float, rate: float, months: int) -> dict:
    monthly_rate = rate / 100 / 12
    if monthly_rate == 0:
        return {"principal": debt, "interest": 0, "total": debt}

    if months <= 0:
        return {"error": "Срок должен быть больше 0"}

    monthly_payment = debt * monthly_rate / (1 - (1 + monthly_rate) ** (-months))
    total_paid = monthly_payment * months
    interest = total_paid - debt

    return {
        "principal": round(debt, 2),
        "interest": round(interest, 2),
        "total": round(total_paid, 2),
        "monthly_payment": round(monthly_payment, 2),
    }


def calculate_credit_risk(limit: float, used: float, rate: float) -> dict:
    if limit <= 0:
        return {"error": "Лимит должен быть больше 0"}

    usage_pct = (used / limit) * 100

    if usage_pct < 30:
        risk_level = "🟢 Низкий"
        recommendation = "Нагрузка на карту в норме. Старайтесь не превышать 30% лимита."
    elif usage_pct < 70:
        risk_level = "🟡 Средний"
        recommendation = "Нагрузка умеренная. Рекомендуем погасить часть долга для снижения процентов."
    else:
        risk_level = "🔴 Высокий"
        recommendation = "Карта почти исчерпана. Приоритет — погашение долга. Избегайте новых трат по этой карте."

    monthly_interest = used * (rate / 100 / 12)

    return {
        "risk_level": risk_level,
        "usage_pct": round(usage_pct, 1),
        "monthly_interest": round(monthly_interest, 2),
        "recommendation": recommendation,
    }


def calculate_goal_months(target_amount: float, monthly_saving: float) -> dict:
    if monthly_saving <= 0:
        return {"error": "Сумма накопления должна быть больше 0"}
    if target_amount <= 0:
        return {"error": "Целевая сумма должна быть больше 0"}

    months = math.ceil(target_amount / monthly_saving)
    years = months // 12
    rem_months = months % 12

    if years > 0:
        period = f"{years} лет {rem_months} месяцев" if rem_months else f"{years} лет"
    else:
        period = f"{months} месяцев"

    return {
        "months": months,
        "period": period,
    }


def calculate_financial_score(profile: dict) -> tuple[int, str]:
    score = 50

    spending_map = {
        "Трачу с умом": 15,
        "Иногда трачу лишнее": 5,
        "Часто покупаю ненужное": -10,
        "Почти не контролирую расходы": -20,
    }
    score += spending_map.get(profile.get("spending_style", ""), 0)

    impulsive_map = {
        "Нет, редко": 10,
        "Иногда": 0,
        "Часто": -10,
        "Да, это моя главная проблема": -20,
    }
    score += impulsive_map.get(profile.get("impulsive_spending", ""), 0)

    tracking_map = {
        "Да, регулярно": 15,
        "Иногда": 5,
        "Нет": -5,
        "Пробовал, но бросил": 0,
    }
    score += tracking_map.get(profile.get("expense_tracking", ""), 0)

    debts_map = {
        "Нет": 10,
        "Есть кредитка": -5,
        "Есть кредит": -10,
        "Есть рассрочка": -5,
        "Есть несколько долгов": -20,
    }
    score += debts_map.get(profile.get("debts_status", ""), 0)

    salary_map = {
        "Не остается вообще": -15,
        "Остаюсь примерно в ноль": -5,
        "Иногда немного остается": 5,
        "Удается откладывать": 15,
    }
    score += salary_map.get(profile.get("salary_end_status", ""), 0)

    score = max(5, min(95, score))

    if score < 30:
        main_risk = "Критическая нехватка бюджета до зарплаты"
    elif score < 50:
        main_risk = "Высокий риск долговой нагрузки"
    elif score < 70:
        main_risk = "Нестабильное финансовое положение"
    elif score < 85:
        main_risk = "Умеренный контроль расходов"
    else:
        main_risk = "Хорошая финансовая дисциплина"

    return score, main_risk


def snowball_debt_plan(cards: list) -> str:
    if not cards:
        return "Нет данных о долгах."

    sorted_cards = sorted(cards, key=lambda c: c["debt_amount"])
    lines = ["📋 <b>План выхода из долгов (метод снежного кома)</b>\n"]
    lines.append("Стратегия: сначала закрываем самый маленький долг, потом добавляем освободившийся платеж к следующему.\n")

    for i, card in enumerate(sorted_cards, 1):
        lines.append(
            f"{i}. <b>{card['card_name']}</b>\n"
            f"   Долг: {card['debt_amount']:,.0f} ₽ | Ставка: {card['interest_rate']}% | "
            f"Мин. платеж: {card['min_payment']:,.0f} ₽"
        )

    total_debt = sum(c["debt_amount"] for c in cards)
    total_min = sum(c["min_payment"] for c in cards)

    lines.append(f"\n💰 Общий долг: {total_debt:,.0f} ₽")
    lines.append(f"📅 Минимальные платежи в месяц: {total_min:,.0f} ₽")
    lines.append(
        f"\n💡 <b>Рекомендация:</b> Платите минимум по всем картам, "
        f"но добавьте любую свободную сумму к первому долгу. "
        f"После его закрытия — перенаправьте весь освободившийся платеж на следующий."
    )

    return "\n".join(lines)
