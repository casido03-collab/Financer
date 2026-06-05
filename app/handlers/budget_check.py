from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from app.database import db
from app.database.analytics import record_section, record_budget_check
from app.handlers.states import BudgetCheckFSM
from app.keyboards.reply import cancel_kb, back_to_menu_kb
from app.services.finance_calculators import calculate_daily_limit

router = Router()


@router.message(F.text == "📊 Проверка бюджета")
async def budget_check_start(message: Message, state: FSMContext):
    await state.clear()
    user = await db.get_user(message.from_user.id)
    if user:
        await record_section(user["id"], "📊 Проверка бюджета")
    await state.set_state(BudgetCheckFSM.amount)
    await message.answer(
        "📊 <b>Проверка бюджета</b>\n\n"
        "Сколько денег у Вас осталось прямо сейчас?\n\n"
        "Введите сумму в рублях (только цифры):",
        reply_markup=cancel_kb(),
        parse_mode="HTML",
    )


@router.message(BudgetCheckFSM.amount)
async def budget_check_amount(message: Message, state: FSMContext):
    if message.text in ("❌ Отмена", "⬅️ Главное меню"):
        await state.clear()
        from app.handlers.menu import send_main_menu
        user = await db.get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
        await send_main_menu(message, user)
        return

    try:
        amount = float(message.text.replace(" ", "").replace(",", ".").replace("₽", ""))
        if amount < 0:
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введите корректную сумму (только цифры).", reply_markup=cancel_kb())
        return

    await state.update_data(amount=amount)
    await state.set_state(BudgetCheckFSM.days)
    await message.answer(
        "Через сколько дней зарплата?\n\nВведите число дней:",
        reply_markup=cancel_kb(),
    )


@router.message(BudgetCheckFSM.days)
async def budget_check_days(message: Message, state: FSMContext):
    if message.text in ("❌ Отмена", "⬅️ Главное меню"):
        await state.clear()
        from app.handlers.menu import send_main_menu
        user = await db.get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
        await send_main_menu(message, user)
        return

    try:
        days = int(message.text.strip())
        if days <= 0 or days > 60:
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число дней (от 1 до 60).", reply_markup=cancel_kb())
        return

    data = await state.get_data()
    await state.clear()

    amount = data["amount"]
    result = calculate_daily_limit(amount, days)

    text = (
        f"📊 <b>Проверка бюджета</b>\n\n"
        f"Остаток: <b>{amount:,.0f} ₽</b>\n"
        f"До зарплаты: <b>{days} дней</b>\n\n"
        f"Ваш дневной лимит:\n"
        f"<b>{result['daily_limit']:,.0f} ₽ в день</b>\n\n"
        f"Уровень риска: {result['risk']}\n\n"
        f"💡 Рекомендация:\n{result['recommendation']}"
    )

    user = await db.get_user(message.from_user.id)
    if user:
        await record_budget_check(user["id"])
        await db.save_consultation(
            user_id=user["id"],
            consultation_type="budget_check",
            input_data=f"Остаток: {amount} ₽, дней до зарплаты: {days}",
            ai_response=text,
            is_paid=False,
        )

    await message.answer(text, reply_markup=back_to_menu_kb(), parse_mode="HTML")
