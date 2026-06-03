from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.database import db
from app.handlers.states import GoalFSM
from app.keyboards.reply import cancel_kb, goal_actions_kb, back_to_menu_kb
from app.keyboards.inline import confirm_goal_kb
from app.services.finance_calculators import calculate_goal_months

router = Router()


@router.message(F.text == "🎯 Моя цель")
async def goals_start(message: Message, state: FSMContext):
    await state.clear()
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Сначала запустите бота командой /start")
        return

    goal = await db.get_goal(user["id"])
    if goal:
        result = calculate_goal_months(goal["target_amount"], goal["monthly_saving"])
        text = (
            f"🎯 <b>Ваша цель: {goal['goal_name']}</b>\n\n"
            f"Сумма: {goal['target_amount']:,.0f} ₽\n"
            f"Ежемесячно: {goal['monthly_saving']:,.0f} ₽\n\n"
            f"Вы достигнете цели примерно через:\n"
            f"<b>{result.get('period', '—')}</b>"
        )
        await message.answer(text, reply_markup=goal_actions_kb(), parse_mode="HTML")
    else:
        await message.answer(
            "🎯 <b>Моя цель</b>\n\nУ Вас пока нет финансовой цели.\nДавайте поставим её!",
            reply_markup=cancel_kb(),
            parse_mode="HTML",
        )
        await _ask_goal_name(message, state)


async def _ask_goal_name(message: Message, state: FSMContext):
    await state.set_state(GoalFSM.goal_name)
    await message.answer("На что Вы хотите накопить?\n\nНапример: автомобиль, ремонт, отпуск, подушка безопасности.", reply_markup=cancel_kb())


@router.message(F.text == "✏️ Изменить цель")
async def edit_goal(message: Message, state: FSMContext):
    await _ask_goal_name(message, state)


@router.message(GoalFSM.goal_name)
async def goal_name_handler(message: Message, state: FSMContext):
    if message.text in ("❌ Отмена", "⬅️ Главное меню"):
        await state.clear()
        from app.handlers.menu import send_main_menu
        user = await db.get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
        await send_main_menu(message, user)
        return

    if not message.text or len(message.text.strip()) < 2:
        await message.answer("Пожалуйста, введите название цели.", reply_markup=cancel_kb())
        return

    await state.update_data(goal_name=message.text.strip())
    await state.set_state(GoalFSM.target_amount)
    await message.answer("Какая сумма Вам нужна (в рублях)?", reply_markup=cancel_kb())


@router.message(GoalFSM.target_amount)
async def goal_amount_handler(message: Message, state: FSMContext):
    if message.text in ("❌ Отмена", "⬅️ Главное меню"):
        await state.clear()
        from app.handlers.menu import send_main_menu
        user = await db.get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
        await send_main_menu(message, user)
        return

    try:
        amount = float(message.text.replace(" ", "").replace(",", ".").replace("₽", ""))
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Введите корректную сумму (только цифры).", reply_markup=cancel_kb())
        return

    await state.update_data(target_amount=amount)
    await state.set_state(GoalFSM.monthly_saving)
    await message.answer("Сколько Вы можете откладывать в месяц (в рублях)?", reply_markup=cancel_kb())


@router.message(GoalFSM.monthly_saving)
async def goal_saving_handler(message: Message, state: FSMContext):
    if message.text in ("❌ Отмена", "⬅️ Главное меню"):
        await state.clear()
        from app.handlers.menu import send_main_menu
        user = await db.get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
        await send_main_menu(message, user)
        return

    try:
        saving = float(message.text.replace(" ", "").replace(",", ".").replace("₽", ""))
        if saving <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Введите корректную сумму (только цифры, больше 0).", reply_markup=cancel_kb())
        return

    data = await state.get_data()
    await state.update_data(monthly_saving=saving)
    data["monthly_saving"] = saving

    result = calculate_goal_months(data["target_amount"], saving)

    text = (
        f"🎯 <b>Ваша цель: {data['goal_name']}</b>\n\n"
        f"Сумма: {data['target_amount']:,.0f} ₽\n"
        f"Ежемесячно: {saving:,.0f} ₽\n\n"
        f"Вы достигнете цели примерно через:\n"
        f"<b>{result.get('period', '—')}</b>"
    )

    await message.answer(text, reply_markup=confirm_goal_kb(), parse_mode="HTML")


@router.callback_query(F.data == "goal_confirm")
async def goal_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    user = await db.get_user(callback.from_user.id)
    if not user:
        await callback.answer("Ошибка. Попробуйте снова.")
        return

    await db.save_goal(
        user_id=user["id"],
        goal_name=data["goal_name"],
        target_amount=data["target_amount"],
        monthly_saving=data["monthly_saving"],
    )

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        "✅ Цель сохранена! Удачи в накоплениях!",
        reply_markup=goal_actions_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "goal_edit")
async def goal_edit_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer()
    await _ask_goal_name(callback.message, state)


@router.message(F.text == "📊 Проверить прогресс")
async def goal_progress(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Сначала запустите бота командой /start")
        return

    goal = await db.get_goal(user["id"])
    if not goal:
        await message.answer("У Вас нет сохранённой цели.", reply_markup=back_to_menu_kb())
        return

    result = calculate_goal_months(goal["target_amount"], goal["monthly_saving"])
    text = (
        f"📊 <b>Прогресс по цели</b>\n\n"
        f"🎯 Цель: {goal['goal_name']}\n"
        f"Целевая сумма: {goal['target_amount']:,.0f} ₽\n"
        f"Ежемесячные накопления: {goal['monthly_saving']:,.0f} ₽\n\n"
        f"До достижения цели: <b>{result.get('period', '—')}</b>\n\n"
        f"💡 Совет: Если увеличить ежемесячные накопления хотя бы на 10%, срок сократится заметно."
    )
    await message.answer(text, reply_markup=goal_actions_kb(), parse_mode="HTML")
