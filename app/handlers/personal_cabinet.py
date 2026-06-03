from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime

from app.database import db
from app.keyboards.reply import personal_cabinet_kb, back_to_menu_kb, cancel_kb
from app.keyboards.inline import credit_cards_list_kb, card_actions_kb
from app.handlers.states import AddCardFSM
from app.services.user_profile import build_profile_text

router = Router()


@router.message(F.text == "👤 Личный кабинет")
async def personal_cabinet(message: Message, state: FSMContext):
    await state.clear()
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Сначала запустите бота командой /start")
        return

    profile = await db.get_user_profile(user["id"])
    goal = await db.get_goal(user["id"])
    cards = await db.get_credit_cards(user["id"])
    days = await db.get_days_with_bot(user["id"])
    budget_checks = await db.get_budget_checks_count(user["id"])
    free_consults = await db.count_free_consultations(user["id"])

    tariff = user.get("tariff", "free")
    sub_until = user.get("subscription_until")
    if tariff == "premium" and sub_until:
        try:
            until_dt = datetime.fromisoformat(sub_until)
            if until_dt > datetime.utcnow():
                tariff_text = "💎 Премиум"
                date_text = until_dt.strftime("%d.%m.%Y")
            else:
                tariff_text = "🔓 Бесплатный"
                date_text = "—"
        except Exception:
            tariff_text = "🔓 Бесплатный"
            date_text = "—"
    else:
        tariff_text = "🔓 Бесплатный"
        date_text = "—"

    max_free = 1
    consults_left = max_free - min(free_consults, max_free)
    budget_plan_status = "✅ Доступно" if tariff == "premium" else "🔒 Только план на 5 дней"

    score = profile.get("financial_score", 0) if profile else 0
    income = profile.get("income_range", "—") if profile else "—"
    salary_end = profile.get("salary_end_status", "—") if profile else "—"

    if goal:
        from app.services.finance_calculators import calculate_goal_months
        result = calculate_goal_months(goal["target_amount"], goal["monthly_saving"])
        goal_text = f"{goal['goal_name']} — {goal['target_amount']:,.0f} ₽ ({result.get('period', '—')})"
    else:
        goal_text = "Не установлена"

    cards_text = f"{len(cards)} карт(ы)" if cards else "Не добавлены"

    text = (
        f"👤 <b>Личный кабинет</b>\n\n"
        f"Ваш тариф: {tariff_text}\n"
        f"Доступ до: {date_text}\n"
        f"Осталось консультаций: {consults_left}\n"
        f"Планирование бюджета: {budget_plan_status}\n\n"
        f"📊 <b>Финансовый профиль:</b>\n"
        f"Доход: {income}\n"
        f"Перед зарплатой: {salary_end}\n"
        f"Финансовая устойчивость: {score}/100\n\n"
        f"🎯 <b>Текущая цель:</b>\n{goal_text}\n\n"
        f"💳 <b>Кредитные карты:</b>\n{cards_text}\n\n"
        f"🏆 <b>Прогресс:</b>\n"
        f"Дней с ботом: {days}\n"
        f"Проверок бюджета: {budget_checks}"
    )

    await message.answer(text, reply_markup=personal_cabinet_kb(), parse_mode="HTML")


@router.message(F.text == "📊 Мой финансовый профиль")
async def show_profile(message: Message, state: FSMContext):
    await state.clear()
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Сначала запустите бота командой /start")
        return
    text = await build_profile_text(user)
    await message.answer(text, reply_markup=personal_cabinet_kb(), parse_mode="HTML")


@router.message(F.text == "📜 История консультаций")
async def consultation_history(message: Message, state: FSMContext):
    await state.clear()
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Сначала запустите бота командой /start")
        return

    consultations = await db.get_consultations(user["id"], limit=5)
    if not consultations:
        await message.answer("У Вас пока нет консультаций.", reply_markup=personal_cabinet_kb())
        return

    type_names = {
        "plan_5_days": "📋 План на 5 дней",
        "plan_14_days": "📋 План на 14 дней",
        "budget_check": "📊 Проверка бюджета",
        "expense_analysis": "💸 Анализ расходов",
    }

    lines = ["📜 <b>История консультаций</b>\n"]
    for c in consultations:
        try:
            dt = datetime.fromisoformat(c["created_at"]).strftime("%d.%m.%Y %H:%M")
        except Exception:
            dt = "—"
        ctype = type_names.get(c["consultation_type"], c["consultation_type"])
        paid_tag = "⭐ Платная" if c["is_paid"] else "🆓 Бесплатная"
        lines.append(f"• {dt} | {ctype} | {paid_tag}")

    await message.answer("\n".join(lines), reply_markup=personal_cabinet_kb(), parse_mode="HTML")


@router.message(F.text == "💳 Мои кредитки")
async def my_credit_cards(message: Message, state: FSMContext):
    await state.clear()
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Сначала запустите бота командой /start")
        return

    cards = await db.get_credit_cards(user["id"])
    if not cards:
        await message.answer(
            "💳 <b>Мои кредитные карты</b>\n\nУ Вас нет сохранённых карт.",
            reply_markup=credit_cards_list_kb([]),
            parse_mode="HTML",
        )
    else:
        await message.answer(
            f"💳 <b>Мои кредитные карты</b>\n\nСохранено: {len(cards)} карт(ы).",
            reply_markup=credit_cards_list_kb(cards),
            parse_mode="HTML",
        )


@router.callback_query(F.data == "card_add")
async def add_card_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddCardFSM.card_name)
    await callback.message.answer("Введите название карты (например: Тинькофф, Сбер, ВТБ):", reply_markup=cancel_kb())
    await callback.answer()


@router.message(AddCardFSM.card_name)
async def add_card_name(message: Message, state: FSMContext):
    if message.text in ("❌ Отмена", "⬅️ Главное меню"):
        await state.clear()
        from app.handlers.menu import send_main_menu
        user = await db.get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
        await send_main_menu(message, user)
        return
    await state.update_data(card_name=message.text.strip())
    await state.set_state(AddCardFSM.debt)
    await message.answer("Текущий долг по карте (в рублях):", reply_markup=cancel_kb())


@router.message(AddCardFSM.debt)
async def add_card_debt(message: Message, state: FSMContext):
    if message.text in ("❌ Отмена", "⬅️ Главное меню"):
        await state.clear()
        from app.handlers.menu import send_main_menu
        user = await db.get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
        await send_main_menu(message, user)
        return
    try:
        debt = float(message.text.replace(" ", "").replace(",", ".").replace("₽", ""))
        if debt < 0:
            raise ValueError
    except ValueError:
        await message.answer("Введите корректную сумму.", reply_markup=cancel_kb())
        return
    await state.update_data(debt=debt)
    await state.set_state(AddCardFSM.rate)
    await message.answer("Процентная ставка (% годовых):", reply_markup=cancel_kb())


@router.message(AddCardFSM.rate)
async def add_card_rate(message: Message, state: FSMContext):
    if message.text in ("❌ Отмена", "⬅️ Главное меню"):
        await state.clear()
        from app.handlers.menu import send_main_menu
        user = await db.get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
        await send_main_menu(message, user)
        return
    try:
        rate = float(message.text.replace("%", "").replace(",", "."))
        if rate < 0 or rate > 200:
            raise ValueError
    except ValueError:
        await message.answer("Введите корректную ставку (0-200%).", reply_markup=cancel_kb())
        return
    await state.update_data(rate=rate)
    await state.set_state(AddCardFSM.min_payment)
    await message.answer("Минимальный ежемесячный платеж (в рублях):", reply_markup=cancel_kb())


@router.message(AddCardFSM.min_payment)
async def add_card_min_payment(message: Message, state: FSMContext):
    if message.text in ("❌ Отмена", "⬅️ Главное меню"):
        await state.clear()
        from app.handlers.menu import send_main_menu
        user = await db.get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
        await send_main_menu(message, user)
        return
    try:
        min_pay = float(message.text.replace(" ", "").replace(",", ".").replace("₽", ""))
        if min_pay < 0:
            raise ValueError
    except ValueError:
        await message.answer("Введите корректную сумму.", reply_markup=cancel_kb())
        return

    data = await state.get_data()
    await state.clear()

    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Ошибка. Попробуйте снова.")
        return

    await db.save_credit_card(
        user_id=user["id"],
        card_name=data["card_name"],
        debt_amount=data["debt"],
        interest_rate=data["rate"],
        min_payment=min_pay,
    )

    await message.answer(
        f"✅ Карта <b>{data['card_name']}</b> сохранена!\n"
        f"Долг: {data['debt']:,.0f} ₽ | Ставка: {data['rate']}%",
        reply_markup=personal_cabinet_kb(),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("card_view_"))
async def view_card(callback: CallbackQuery):
    card_id = int(callback.data.split("_")[-1])
    user = await db.get_user(callback.from_user.id)
    if not user:
        await callback.answer("Ошибка.")
        return

    cards = await db.get_credit_cards(user["id"])
    card = next((c for c in cards if c["id"] == card_id), None)
    if not card:
        await callback.answer("Карта не найдена.")
        return

    text = (
        f"💳 <b>{card['card_name']}</b>\n\n"
        f"Долг: {card['debt_amount']:,.0f} ₽\n"
        f"Ставка: {card['interest_rate']}% годовых\n"
        f"Мин. платеж: {card['min_payment']:,.0f} ₽"
    )
    await callback.message.answer(text, reply_markup=card_actions_kb(card_id), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("card_delete_"))
async def delete_card(callback: CallbackQuery):
    card_id = int(callback.data.split("_")[-1])
    user = await db.get_user(callback.from_user.id)
    if user:
        await db.delete_credit_card(card_id, user["id"])
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("🗑️ Карта удалена.", reply_markup=personal_cabinet_kb())
    await callback.answer()


@router.callback_query(F.data == "cards_back")
async def cards_back(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    cards = await db.get_credit_cards(user["id"]) if user else []
    await callback.message.edit_reply_markup(reply_markup=credit_cards_list_kb(cards))
    await callback.answer()


@router.message(F.text == "⚙️ Изменить данные")
async def edit_profile_start(message: Message, state: FSMContext):
    await message.answer(
        "⚙️ Чтобы обновить финансовый профиль, пройдите диагностику заново.\n\nКоманда: /start",
        reply_markup=personal_cabinet_kb(),
    )
