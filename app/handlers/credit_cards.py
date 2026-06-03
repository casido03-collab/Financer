from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.database import db
from app.handlers.states import CreditCalcFSM, AddCardFSM
from app.keyboards.reply import credit_cards_menu_kb, cancel_kb, back_to_menu_kb
from app.keyboards.inline import credit_cards_list_kb, card_actions_kb
from app.services.finance_calculators import (
    calculate_credit_payment, calculate_debt_closure,
    calculate_overpayment, calculate_credit_risk, snowball_debt_plan,
)
from app.services.openai_service import generate_debt_plan

router = Router()


@router.message(F.text == "💳 Кредитные карты")
async def credit_cards_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "💳 <b>Помощник по кредитным картам</b>\n\n"
        "Помогу понять, сколько Вы переплачиваете, когда закроете долг "
        "и как быстрее выбраться из кредитной нагрузки.",
        reply_markup=credit_cards_menu_kb(),
        parse_mode="HTML",
    )


@router.message(F.text == "🧮 Рассчитать платеж")
async def calc_payment_start(message: Message, state: FSMContext):
    await state.set_state(CreditCalcFSM.debt)
    await state.update_data(mode="payment")
    await message.answer("Введите сумму долга по карте (в рублях):", reply_markup=cancel_kb())


@router.message(F.text == "📅 Когда закрою долг")
async def calc_closure_start(message: Message, state: FSMContext):
    await state.set_state(CreditCalcFSM.debt)
    await state.update_data(mode="closure")
    await message.answer("Введите сумму долга (в рублях):", reply_markup=cancel_kb())


@router.message(F.text == "💸 Сколько переплачу")
async def calc_overpayment_start(message: Message, state: FSMContext):
    await state.set_state(CreditCalcFSM.debt)
    await state.update_data(mode="overpayment")
    await message.answer("Введите сумму долга (в рублях):", reply_markup=cancel_kb())


@router.message(F.text == "⚠️ Риск кредитки")
async def calc_risk_start(message: Message, state: FSMContext):
    await state.set_state(CreditCalcFSM.limit)
    await state.update_data(mode="risk")
    await message.answer("Введите лимит Вашей кредитной карты (в рублях):", reply_markup=cancel_kb())


@router.message(CreditCalcFSM.limit)
async def credit_calc_limit(message: Message, state: FSMContext):
    if message.text in ("❌ Отмена", "⬅️ Главное меню"):
        await _cancel(message, state)
        return
    try:
        limit = float(message.text.replace(" ", "").replace(",", ".").replace("₽", ""))
        if limit <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Введите корректную сумму.", reply_markup=cancel_kb())
        return

    await state.update_data(limit=limit)
    await state.set_state(CreditCalcFSM.used)
    await message.answer("Сколько использовано (текущий долг, в рублях)?", reply_markup=cancel_kb())


@router.message(CreditCalcFSM.used)
async def credit_calc_used(message: Message, state: FSMContext):
    if message.text in ("❌ Отмена", "⬅️ Главное меню"):
        await _cancel(message, state)
        return
    try:
        used = float(message.text.replace(" ", "").replace(",", ".").replace("₽", ""))
        if used < 0:
            raise ValueError
    except ValueError:
        await message.answer("Введите корректную сумму.", reply_markup=cancel_kb())
        return

    data = await state.get_data()
    await state.update_data(used=used)
    await state.set_state(CreditCalcFSM.rate)
    await message.answer("Укажите процентную ставку по карте (% годовых):", reply_markup=cancel_kb())


@router.message(CreditCalcFSM.debt)
async def credit_calc_debt(message: Message, state: FSMContext):
    if message.text in ("❌ Отмена", "⬅️ Главное меню"):
        await _cancel(message, state)
        return
    try:
        debt = float(message.text.replace(" ", "").replace(",", ".").replace("₽", ""))
        if debt <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Введите корректную сумму долга.", reply_markup=cancel_kb())
        return

    await state.update_data(debt=debt)
    await state.set_state(CreditCalcFSM.rate)
    await message.answer("Укажите процентную ставку (% годовых):", reply_markup=cancel_kb())


@router.message(CreditCalcFSM.rate)
async def credit_calc_rate(message: Message, state: FSMContext):
    if message.text in ("❌ Отмена", "⬅️ Главное меню"):
        await _cancel(message, state)
        return
    try:
        rate = float(message.text.replace(" ", "").replace(",", ".").replace("%", ""))
        if rate < 0 or rate > 200:
            raise ValueError
    except ValueError:
        await message.answer("Введите корректную ставку (от 0 до 200%).", reply_markup=cancel_kb())
        return

    await state.update_data(rate=rate)
    data = await state.get_data()
    mode = data.get("mode")

    if mode == "risk":
        result = calculate_credit_risk(data["limit"], data["used"], rate)
        text = (
            f"⚠️ <b>Риск кредитной карты</b>\n\n"
            f"Уровень риска: {result['risk_level']}\n"
            f"Использовано лимита: {result['usage_pct']}%\n"
            f"Ежемесячные проценты: ~{result['monthly_interest']:,.0f} ₽\n\n"
            f"💡 {result['recommendation']}"
        )
        await state.clear()
        await message.answer(text, reply_markup=credit_cards_menu_kb(), parse_mode="HTML")
        return

    if mode == "overpayment":
        await state.set_state(CreditCalcFSM.months)
        await message.answer("На сколько месяцев рассчитан кредит?", reply_markup=cancel_kb())
        return

    await state.set_state(CreditCalcFSM.payment)
    label = "Укажите желаемый ежемесячный платеж (в рублях):" if mode == "payment" else "Укажите ежемесячный платеж (в рублях):"
    await message.answer(label, reply_markup=cancel_kb())


@router.message(CreditCalcFSM.months)
async def credit_calc_months(message: Message, state: FSMContext):
    if message.text in ("❌ Отмена", "⬅️ Главное меню"):
        await _cancel(message, state)
        return
    try:
        months = int(message.text.strip())
        if months <= 0 or months > 600:
            raise ValueError
    except ValueError:
        await message.answer("Введите корректное количество месяцев (от 1 до 600).", reply_markup=cancel_kb())
        return

    data = await state.get_data()
    await state.clear()

    result = calculate_overpayment(data["debt"], data["rate"], months)
    if "error" in result:
        await message.answer(f"❌ {result['error']}", reply_markup=credit_cards_menu_kb())
        return

    text = (
        f"💸 <b>Переплата по кредиту</b>\n\n"
        f"Основной долг: {result['principal']:,.0f} ₽\n"
        f"Проценты за весь срок: {result['interest']:,.0f} ₽\n"
        f"Всего банку: {result['total']:,.0f} ₽\n"
        f"Ежемесячный платеж: {result['monthly_payment']:,.0f} ₽"
    )
    await message.answer(text, reply_markup=credit_cards_menu_kb(), parse_mode="HTML")


@router.message(CreditCalcFSM.payment)
async def credit_calc_payment(message: Message, state: FSMContext):
    if message.text in ("❌ Отмена", "⬅️ Главное меню"):
        await _cancel(message, state)
        return
    try:
        payment = float(message.text.replace(" ", "").replace(",", ".").replace("₽", ""))
        if payment <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Введите корректную сумму платежа.", reply_markup=cancel_kb())
        return

    data = await state.get_data()
    await state.clear()
    mode = data["mode"]
    debt = data["debt"]
    rate = data["rate"]

    if mode == "payment":
        result = calculate_credit_payment(debt, rate, payment)
    else:
        result = calculate_debt_closure(debt, payment, rate)

    if "error" in result and not result.get("warning"):
        await message.answer(f"❌ {result['error']}", reply_markup=credit_cards_menu_kb())
        return

    warning = result.get("warning", "")
    text = (
        f"🧮 <b>Расчет кредитного платежа</b>\n\n"
        f"Долг: {debt:,.0f} ₽ | Ставка: {rate}%\n"
        f"Платеж: {payment:,.0f} ₽/мес\n\n"
        f"Срок закрытия: <b>{result['months']} месяцев</b>\n"
        f"Переплата: {result['overpayment']:,.0f} ₽\n"
        f"Всего выплат: {result['total_paid']:,.0f} ₽"
    )
    if warning:
        text += f"\n\n⚠️ {warning}"
    if result.get("recommendation"):
        text += f"\n\n💡 {result['recommendation']}"

    await message.answer(text, reply_markup=credit_cards_menu_kb(), parse_mode="HTML")


@router.message(F.text == "📋 План выхода из долгов")
async def debt_plan_start(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Сначала запустите бота командой /start")
        return

    cards = await db.get_credit_cards(user["id"])
    if not cards:
        await message.answer(
            "У Вас нет сохранённых кредитных карт.\n\n"
            "Перейдите в раздел 💳 Мои кредитки в Личном кабинете, чтобы добавить карты.",
            reply_markup=credit_cards_menu_kb(),
        )
        return

    text = snowball_debt_plan(cards)
    await message.answer(text, reply_markup=credit_cards_menu_kb(), parse_mode="HTML")

    profile = await db.get_user_profile(user["id"])
    if profile:
        debt_data = "\n".join(
            f"{c['card_name']}: долг {c['debt_amount']:,.0f} ₽, ставка {c['interest_rate']}%, мин. платеж {c['min_payment']:,.0f} ₽"
            for c in cards
        )
        ai_text = await generate_debt_plan(debt_data, profile)
        await message.answer(
            f"🤖 <b>Персональный анализ от ИИ:</b>\n\n{ai_text}",
            reply_markup=credit_cards_menu_kb(),
            parse_mode="HTML",
        )


async def _cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Действие отменено.", reply_markup=credit_cards_menu_kb())
