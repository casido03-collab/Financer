from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, LabeledPrice
from aiogram.fsm.context import FSMContext

from app.database import db
from app.handlers.states import ConsultationFSM
from app.keyboards.reply import cancel_kb, back_to_menu_kb, consultation_mode_kb
from app.keyboards.inline import upsell_14_days_kb
from app.services.openai_service import generate_5_day_plan, generate_14_day_plan

router = Router()

PLAN_14_PRICE = 200


@router.message(F.text == "💬 Консультация")
async def consultation_start(message: Message, state: FSMContext):
    await state.clear()
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Сначала запустите бота командой /start")
        return

    free_used = await db.count_free_consultations(user["id"])
    has_sub = await db.is_subscription_active(message.from_user.id)

    if has_sub:
        await message.answer(
            "💬 <b>Консультация</b>\n\n"
            "У Вас активна премиум-подписка. Запускаю расширенный план.\n\n"
            "Для начала мне нужны Ваши данные. Введите Ваш текущий доход (в рублях):",
            reply_markup=cancel_kb(),
            parse_mode="HTML",
        )
        await state.update_data(is_paid=True)
        await state.set_state(ConsultationFSM.income)
        return

    if free_used > 0:
        await message.answer(
            "💬 <b>Консультация</b>\n\n"
            "Вы уже использовали бесплатную консультацию.\n\n"
            "Для получения нового персонального плана на 14 дней — оформите подписку.",
            reply_markup=upsell_14_days_kb(),
            parse_mode="HTML",
        )
        return

    await message.answer(
        "💬 <b>Консультация</b>\n\n"
        "Я составлю для Вас бесплатный финансовый план на 5 дней.\n\n"
        "Для начала мне нужно несколько данных.\n\n"
        "Введите Ваш текущий доход (в рублях):",
        reply_markup=cancel_kb(),
        parse_mode="HTML",
    )
    await state.update_data(is_paid=False)
    await state.set_state(ConsultationFSM.income)


@router.message(ConsultationFSM.income)
async def consultation_income(message: Message, state: FSMContext):
    if message.text in ("❌ Отмена", "⬅️ Главное меню"):
        await state.clear()
        from app.handlers.menu import send_main_menu
        user = await db.get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
        await send_main_menu(message, user)
        return

    try:
        income = float(message.text.replace(" ", "").replace(",", ".").replace("₽", ""))
        if income <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Введите корректную сумму дохода (только цифры).", reply_markup=cancel_kb())
        return

    await state.update_data(income=income)
    await state.set_state(ConsultationFSM.balance)
    await message.answer("Сколько денег у Вас осталось прямо сейчас (в рублях)?", reply_markup=cancel_kb())


@router.message(ConsultationFSM.balance)
async def consultation_balance(message: Message, state: FSMContext):
    if message.text in ("❌ Отмена", "⬅️ Главное меню"):
        await state.clear()
        from app.handlers.menu import send_main_menu
        user = await db.get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
        await send_main_menu(message, user)
        return

    try:
        balance = float(message.text.replace(" ", "").replace(",", ".").replace("₽", ""))
        if balance < 0:
            raise ValueError
    except ValueError:
        await message.answer("Введите корректную сумму (только цифры, не меньше 0).", reply_markup=cancel_kb())
        return

    await state.update_data(balance=balance)
    await state.set_state(ConsultationFSM.days_to_salary)
    await message.answer("Через сколько дней Вы получите зарплату?", reply_markup=cancel_kb())


@router.message(ConsultationFSM.days_to_salary)
async def consultation_days(message: Message, state: FSMContext):
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
        await message.answer("Введите корректное число дней (от 1 до 60).", reply_markup=cancel_kb())
        return

    await state.update_data(days_to_salary=days)
    await state.set_state(ConsultationFSM.city)
    await message.answer("В каком городе Вы живёте?", reply_markup=cancel_kb())


@router.message(ConsultationFSM.city)
async def consultation_city(message: Message, state: FSMContext):
    if message.text in ("❌ Отмена", "⬅️ Главное меню"):
        await state.clear()
        from app.handlers.menu import send_main_menu
        user = await db.get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
        await send_main_menu(message, user)
        return

    await state.update_data(city=message.text.strip())
    await state.set_state(ConsultationFSM.family_size)
    await message.answer("Сколько человек в Вашей семье (включая Вас)?", reply_markup=cancel_kb())


@router.message(ConsultationFSM.family_size)
async def consultation_family_size(message: Message, state: FSMContext):
    if message.text in ("❌ Отмена", "⬅️ Главное меню"):
        await state.clear()
        from app.handlers.menu import send_main_menu
        user = await db.get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
        await send_main_menu(message, user)
        return

    try:
        size = int(message.text.strip())
        if size <= 0 or size > 20:
            raise ValueError
    except ValueError:
        await message.answer("Введите корректное число человек (от 1 до 20).", reply_markup=cancel_kb())
        return

    await state.update_data(family_size=size)
    await state.set_state(ConsultationFSM.ages)
    await message.answer(
        "Укажите возраст членов семьи (через запятую).\nНапример: 35, 32, 7",
        reply_markup=cancel_kb(),
    )


@router.message(ConsultationFSM.ages)
async def consultation_ages(message: Message, state: FSMContext):
    if message.text in ("❌ Отмена", "⬅️ Главное меню"):
        await state.clear()
        from app.handlers.menu import send_main_menu
        user = await db.get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
        await send_main_menu(message, user)
        return

    await state.update_data(ages=message.text.strip())
    await state.set_state(ConsultationFSM.has_children)
    await message.answer("Есть ли у Вас дети?", reply_markup=cancel_kb())


@router.message(ConsultationFSM.has_children)
async def consultation_children(message: Message, state: FSMContext):
    if message.text in ("❌ Отмена", "⬅️ Главное меню"):
        await state.clear()
        from app.handlers.menu import send_main_menu
        user = await db.get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
        await send_main_menu(message, user)
        return

    await state.update_data(has_children=message.text.strip())
    await state.set_state(ConsultationFSM.mandatory_payments)
    await message.answer(
        "Есть ли у Вас обязательные платежи в ближайшие 5 дней?\n\n"
        "Например: аренда 15000, кредит 5000. Или напишите 'Нет'.",
        reply_markup=cancel_kb(),
    )


@router.message(ConsultationFSM.mandatory_payments)
async def consultation_mandatory(message: Message, state: FSMContext):
    if message.text in ("❌ Отмена", "⬅️ Главное меню"):
        await state.clear()
        from app.handlers.menu import send_main_menu
        user = await db.get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
        await send_main_menu(message, user)
        return

    await state.update_data(mandatory_payments=message.text.strip())
    data = await state.get_data()
    is_paid = data.get("is_paid", False)

    await state.set_state(ConsultationFSM.waiting_result)
    await message.answer("⏳ Формирую Ваш финансовый план...", reply_markup=cancel_kb())

    user_data = {
        "Доход": f"{data.get('income', 0):,.0f} ₽",
        "Текущий остаток": f"{data.get('balance', 0):,.0f} ₽",
        "Дней до зарплаты": data.get("days_to_salary", 0),
        "Город": data.get("city", "—"),
        "Членов семьи": data.get("family_size", 1),
        "Возраст членов семьи": data.get("ages", "—"),
        "Дети": data.get("has_children", "—"),
        "Обязательные платежи": data.get("mandatory_payments", "Нет"),
    }

    user = await db.get_user(message.from_user.id)
    profile = await db.get_user_profile(user["id"]) if user else {}
    if profile:
        user_data["Доход (профиль)"] = profile.get("income_range", "—")
        user_data["Долги"] = profile.get("debts_status", "—")

    if is_paid:
        ai_response = await generate_14_day_plan(user_data)
        plan_days = 14
    else:
        ai_response = await generate_5_day_plan(user_data)
        plan_days = 5

    await state.clear()

    if user:
        await db.save_consultation(
            user_id=user["id"],
            consultation_type=f"plan_{plan_days}_days",
            input_data=str(user_data),
            ai_response=ai_response,
            is_paid=is_paid,
        )

    await message.answer(ai_response, reply_markup=back_to_menu_kb(), parse_mode="HTML")

    if not is_paid:
        await message.answer(
            "Хотите получить подробный план расходов на 14 дней?\n\n"
            "Он поможет заранее распределить деньги до зарплаты и снизить риск остаться без средств.\n\n"
            "Стоимость: 200 ⭐",
            reply_markup=upsell_14_days_kb(),
        )
