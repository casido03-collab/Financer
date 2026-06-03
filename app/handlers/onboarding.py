from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from app.database import db
from app.handlers.states import OnboardingFSM
from app.keyboards.reply import (
    work_type_kb, income_range_kb, spending_style_kb, financial_literacy_kb,
    impulsive_spending_kb, expense_tracking_kb, debts_status_kb,
    salary_end_status_kb, money_before_salary_kb, open_menu_kb,
)
from app.services.finance_calculators import calculate_financial_score
from app.services.typing import typing

router = Router()

WORK_TYPES = [
    "👨‍💼 Наемный сотрудник", "🧾 Самозанятый", "🏢 Предприниматель",
    "🎓 Студент", "👵 Пенсионер", "🔎 Временно без работы",
]
INCOME_RANGES = [
    "до 30 000 ₽", "30 000 – 50 000 ₽", "50 000 – 80 000 ₽",
    "80 000 – 120 000 ₽", "120 000 – 200 000 ₽", "более 200 000 ₽",
]
SPENDING_STYLES = [
    "Трачу с умом", "Иногда трачу лишнее",
    "Часто покупаю ненужное", "Почти не контролирую расходы",
]
LITERACIES = [
    "Да, хорошо разбираюсь", "Что-то понимаю",
    "Почти не разбираюсь", "Хочу разобраться с нуля",
]
IMPULSIVE = ["Нет, редко", "Иногда", "Часто", "Да, это моя главная проблема"]
TRACKING = ["Да, регулярно", "Иногда", "Нет", "Пробовал, но бросил"]
DEBTS = ["Нет", "Есть кредитка", "Есть кредит", "Есть рассрочка", "Есть несколько долгов"]
SALARY_END = [
    "Не остается вообще", "Остаюсь примерно в ноль",
    "Иногда немного остается", "Удается откладывать",
]
MONEY_BEFORE = ["0 ₽", "до 1 000 ₽", "1 000 – 5 000 ₽", "5 000 – 10 000 ₽", "больше 10 000 ₽"]


@router.message(F.text == "🚀 Начать диагностику")
async def start_onboarding(message: Message, state: FSMContext):
    await state.set_state(OnboardingFSM.work_type)
    await typing(message, 1.2)
    await message.answer(
        "Кем Вы сейчас работаете?",
        reply_markup=work_type_kb(),
    )


@router.message(OnboardingFSM.work_type)
async def process_work_type(message: Message, state: FSMContext):
    if message.text not in WORK_TYPES:
        await message.answer("Пожалуйста, выберите один из вариантов.", reply_markup=work_type_kb())
        return
    await state.update_data(work_type=message.text)
    await state.set_state(OnboardingFSM.work_sphere)
    await typing(message, 1.5)
    await message.answer(
        "В какой сфере Вы работаете?\n\n"
        "Например: строительство, продажи, IT, медицина, логистика, красота, образование.",
        reply_markup=None,
    )


@router.message(OnboardingFSM.work_sphere)
async def process_work_sphere(message: Message, state: FSMContext):
    if not message.text or len(message.text.strip()) < 2:
        await message.answer("Пожалуйста, введите сферу деятельности.")
        return
    await state.update_data(work_sphere=message.text.strip())
    await state.set_state(OnboardingFSM.income_range)
    await typing(message, 1.3)
    await message.answer(
        "Ваш средний доход за последние 3 месяца?",
        reply_markup=income_range_kb(),
    )


@router.message(OnboardingFSM.income_range)
async def process_income_range(message: Message, state: FSMContext):
    if message.text not in INCOME_RANGES:
        await message.answer("Пожалуйста, выберите один из вариантов.", reply_markup=income_range_kb())
        return
    await state.update_data(income_range=message.text)
    await state.set_state(OnboardingFSM.spending_style)
    await typing(message, 1.4)
    await message.answer(
        "Как Вы оцениваете свои расходы?",
        reply_markup=spending_style_kb(),
    )


@router.message(OnboardingFSM.spending_style)
async def process_spending_style(message: Message, state: FSMContext):
    if message.text not in SPENDING_STYLES:
        await message.answer("Пожалуйста, выберите один из вариантов.", reply_markup=spending_style_kb())
        return
    await state.update_data(spending_style=message.text)
    await state.set_state(OnboardingFSM.financial_literacy)
    await typing(message, 1.3)
    await message.answer(
        "Есть ли у Вас базовая финансовая грамотность?",
        reply_markup=financial_literacy_kb(),
    )


@router.message(OnboardingFSM.financial_literacy)
async def process_financial_literacy(message: Message, state: FSMContext):
    if message.text not in LITERACIES:
        await message.answer("Пожалуйста, выберите один из вариантов.", reply_markup=financial_literacy_kb())
        return
    await state.update_data(financial_literacy=message.text)
    await state.set_state(OnboardingFSM.impulsive_spending)
    await typing(message, 1.5)
    await message.answer(
        "Склонны ли Вы к лишним тратам?",
        reply_markup=impulsive_spending_kb(),
    )


@router.message(OnboardingFSM.impulsive_spending)
async def process_impulsive_spending(message: Message, state: FSMContext):
    if message.text not in IMPULSIVE:
        await message.answer("Пожалуйста, выберите один из вариантов.", reply_markup=impulsive_spending_kb())
        return
    await state.update_data(impulsive_spending=message.text)
    await state.set_state(OnboardingFSM.expense_tracking)
    await typing(message, 1.3)
    await message.answer(
        "Ведёте ли Вы учёт расходов?",
        reply_markup=expense_tracking_kb(),
    )


@router.message(OnboardingFSM.expense_tracking)
async def process_expense_tracking(message: Message, state: FSMContext):
    if message.text not in TRACKING:
        await message.answer("Пожалуйста, выберите один из вариантов.", reply_markup=expense_tracking_kb())
        return
    await state.update_data(expense_tracking=message.text)
    await state.set_state(OnboardingFSM.debts_status)
    await typing(message, 1.4)
    await message.answer(
        "Есть ли у Вас кредиты, рассрочки или кредитные карты?",
        reply_markup=debts_status_kb(),
    )


@router.message(OnboardingFSM.debts_status)
async def process_debts_status(message: Message, state: FSMContext):
    if message.text not in DEBTS:
        await message.answer("Пожалуйста, выберите один из вариантов.", reply_markup=debts_status_kb())
        return
    await state.update_data(debts_status=message.text)
    await state.set_state(OnboardingFSM.salary_end_status)
    await typing(message, 1.3)
    await message.answer(
        "Что обычно происходит с деньгами перед зарплатой?",
        reply_markup=salary_end_status_kb(),
    )


@router.message(OnboardingFSM.salary_end_status)
async def process_salary_end_status(message: Message, state: FSMContext):
    if message.text not in SALARY_END:
        await message.answer("Пожалуйста, выберите один из вариантов.", reply_markup=salary_end_status_kb())
        return
    await state.update_data(salary_end_status=message.text)
    await state.set_state(OnboardingFSM.money_before_salary)
    await typing(message, 1.5)
    await message.answer(
        "Сколько денег обычно остаётся перед зарплатными днями?",
        reply_markup=money_before_salary_kb(),
    )


@router.message(OnboardingFSM.money_before_salary)
async def process_money_before_salary(message: Message, state: FSMContext):
    if message.text not in MONEY_BEFORE:
        await message.answer("Пожалуйста, выберите один из вариантов.", reply_markup=money_before_salary_kb())
        return

    await state.update_data(money_before_salary=message.text)
    data = await state.get_data()
    await state.clear()

    user = await db.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )

    score, main_risk = calculate_financial_score(data)
    data["financial_score"] = score
    data["main_risk"] = main_risk

    await db.save_user_profile(user["id"], data)
    await db.mark_onboarding_complete(message.from_user.id)

    await typing(message, 2.0)
    await message.answer(
        "✅ Диагностика завершена.\n\n"
        "Я сформировал Ваш финансовый профиль.\n\n"
        "Теперь Вы можете получить план расходов, проверить бюджет, "
        "рассчитать кредитные карты или задать вопрос финансовому консультанту.",
        reply_markup=open_menu_kb(),
    )
