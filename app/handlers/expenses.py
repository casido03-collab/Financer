from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from app.database import db
from app.handlers.states import ExpensesFSM
from app.keyboards.reply import (
    expense_analysis_mode_kb, expense_categories_kb, back_to_menu_kb, cancel_kb,
)
from app.services.openai_service import analyze_expenses

router = Router()

CATEGORIES = ["Еда вне дома", "Доставка", "Такси", "Маркетплейсы", "Подписки", "Кредиты", "Развлечения", "Другое"]


@router.message(F.text == "💸 Куда уходят деньги")
async def expenses_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "💸 <b>Куда уходят деньги</b>\n\n"
        "Выберите режим анализа расходов:",
        reply_markup=expense_analysis_mode_kb(),
        parse_mode="HTML",
    )


@router.message(F.text == "📊 Анализ по категориям")
async def expenses_by_categories(message: Message, state: FSMContext):
    await state.set_state(ExpensesFSM.collecting_categories)
    await state.update_data(categories={}, current_category=None)
    await message.answer(
        "Выберите категорию и введите сумму.\n\n"
        "Нажмите на категорию, затем введите сумму расходов за неделю.\n"
        "Когда закончите — нажмите ✅ Готово.",
        reply_markup=expense_categories_kb(),
    )


@router.message(ExpensesFSM.collecting_categories, F.text.in_(CATEGORIES))
async def expense_category_selected(message: Message, state: FSMContext):
    await state.update_data(current_category=message.text)
    await message.answer(
        f"Введите сумму расходов на «{message.text}» за последнюю неделю (в рублях):",
        reply_markup=cancel_kb(),
    )
    await state.set_state(ExpensesFSM.category_input)


@router.message(ExpensesFSM.category_input)
async def expense_amount_input(message: Message, state: FSMContext):
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
        await message.answer("Введите корректную сумму.", reply_markup=cancel_kb())
        return

    data = await state.get_data()
    category = data.get("current_category")
    categories = data.get("categories", {})
    categories[category] = amount
    await state.update_data(categories=categories, current_category=None)
    await state.set_state(ExpensesFSM.collecting_categories)

    saved = ", ".join(f"{k}: {v:,.0f} ₽" for k, v in categories.items())
    await message.answer(
        f"✅ Сохранено: {saved}\n\nВыберите следующую категорию или нажмите ✅ Готово.",
        reply_markup=expense_categories_kb(),
    )


@router.message(ExpensesFSM.collecting_categories, F.text == "✅ Готово")
async def expenses_categories_done(message: Message, state: FSMContext):
    data = await state.get_data()
    categories = data.get("categories", {})

    if not categories:
        await message.answer("Вы не ввели ни одной категории. Выберите хотя бы одну.", reply_markup=expense_categories_kb())
        return

    await state.clear()

    total = sum(categories.values())
    lines = [f"💸 <b>Анализ расходов за неделю</b>\n"]
    sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)

    for cat, amount in sorted_cats:
        pct = (amount / total * 100) if total > 0 else 0
        lines.append(f"• {cat}: {amount:,.0f} ₽ ({pct:.1f}%)")

    lines.append(f"\n<b>Итого за неделю: {total:,.0f} ₽</b>")
    lines.append(f"В месяц (~4 недели): {total * 4:,.0f} ₽")

    top_cat, top_amount = sorted_cats[0]
    lines.append(f"\n⚠️ Наибольшая статья расходов: <b>{top_cat}</b> — {top_amount:,.0f} ₽")

    if total > 0:
        lines.append("\n💡 <b>Рекомендации:</b>")
        if categories.get("Доставка", 0) > 2000:
            lines.append("• Попробуйте готовить дома 2-3 раза в неделю — это сэкономит до 50% на доставке.")
        if categories.get("Такси", 0) > 2000:
            lines.append("• Рассмотрите общественный транспорт хотя бы для части поездок.")
        if categories.get("Маркетплейсы", 0) > 3000:
            lines.append("• Используйте список покупок перед открытием маркетплейса.")
        if categories.get("Еда вне дома", 0) > 3000:
            lines.append("• Еда вне дома — одна из самых дорогих статей. Заменяйте хотя бы часть на домашнюю еду.")

    await message.answer("\n".join(lines), reply_markup=back_to_menu_kb(), parse_mode="HTML")


@router.message(F.text == "✍️ Свободный ввод (ИИ-анализ)")
async def expenses_free_text(message: Message, state: FSMContext):
    await state.set_state(ExpensesFSM.free_text)
    await message.answer(
        "Опишите свои расходы за последнюю неделю в свободной форме.\n\n"
        "Например:\n«За неделю потратил 5000 на доставку, 3000 на такси, 7000 на продукты, 2000 на маркетплейсы.»",
        reply_markup=cancel_kb(),
    )


@router.message(ExpensesFSM.free_text)
async def expenses_free_text_handler(message: Message, state: FSMContext):
    if message.text in ("❌ Отмена", "⬅️ Главное меню"):
        await state.clear()
        from app.handlers.menu import send_main_menu
        user = await db.get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
        await send_main_menu(message, user)
        return

    if not message.text or len(message.text.strip()) < 10:
        await message.answer("Пожалуйста, опишите расходы подробнее.", reply_markup=cancel_kb())
        return

    await state.clear()
    await message.answer("⏳ Анализирую Ваши расходы...", reply_markup=cancel_kb())

    user = await db.get_user(message.from_user.id)
    profile = {}
    if user:
        profile = await db.get_user_profile(user["id"]) or {}

    ai_response = await analyze_expenses(message.text, profile)

    await message.answer(ai_response, reply_markup=back_to_menu_kb(), parse_mode="HTML")

    if user:
        await db.save_consultation(
            user_id=user["id"],
            consultation_type="expense_analysis",
            input_data=message.text,
            ai_response=ai_response,
            is_paid=False,
        )
