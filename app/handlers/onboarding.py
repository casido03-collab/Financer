import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from app.database import db
from app.handlers.states import OnboardingFSM
from app.keyboards.reply import (
    work_type_kb, spending_style_kb,
    impulsive_spending_kb, expense_tracking_kb, open_menu_kb,
)
from app.services.finance_calculators import calculate_financial_score
from app.database.analytics import track_event, touch_user

logger = logging.getLogger(__name__)
router = Router()

WORK_TYPES = [
    "👨‍💼 Наемный сотрудник", "🧾 Самозанятый", "🏢 Предприниматель",
    "🎓 Студент", "👵 Пенсионер", "🔎 Временно без работы",
]
SPENDING_STYLES = [
    "Трачу с умом", "Иногда трачу лишнее",
    "Часто покупаю ненужное", "Почти не контролирую расходы",
]
IMPULSIVE = ["Нет, редко", "Иногда", "Часто", "Да, это моя главная проблема"]
TRACKING  = ["Да, регулярно", "Иногда", "Нет", "Пробовал, но бросил"]


@router.message(F.text == "🚀 Начать диагностику")
async def start_onboarding(message: Message, state: FSMContext):
    await state.set_state(OnboardingFSM.work_type)
    user = await db.get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    await track_event(user["id"], "onboarding_start")
    await message.answer("Кем Вы сейчас работаете?", reply_markup=work_type_kb())


@router.message(OnboardingFSM.work_type)
async def process_work_type(message: Message, state: FSMContext):
    if message.text not in WORK_TYPES:
        await message.answer("Пожалуйста, выберите один из вариантов.", reply_markup=work_type_kb())
        return
    await state.update_data(work_type=message.text)
    await state.set_state(OnboardingFSM.work_sphere)
    await message.answer(
        "В какой сфере Вы работаете?\n\n"
        "Например: строительство, продажи, IT, медицина, логистика, красота, образование.",
    )


@router.message(OnboardingFSM.work_sphere)
async def process_work_sphere(message: Message, state: FSMContext):
    if not message.text or len(message.text.strip()) < 2:
        await message.answer("Пожалуйста, введите сферу деятельности.")
        return
    await state.update_data(work_sphere=message.text.strip())
    await state.set_state(OnboardingFSM.spending_style)
    await message.answer("Как Вы оцениваете свои расходы?", reply_markup=spending_style_kb())


@router.message(OnboardingFSM.spending_style)
async def process_spending_style(message: Message, state: FSMContext):
    if message.text not in SPENDING_STYLES:
        await message.answer("Пожалуйста, выберите один из вариантов.", reply_markup=spending_style_kb())
        return
    await state.update_data(spending_style=message.text)
    await state.set_state(OnboardingFSM.impulsive_spending)
    await message.answer("Склонны ли Вы к лишним тратам?", reply_markup=impulsive_spending_kb())


@router.message(OnboardingFSM.impulsive_spending)
async def process_impulsive_spending(message: Message, state: FSMContext):
    if message.text not in IMPULSIVE:
        await message.answer("Пожалуйста, выберите один из вариантов.", reply_markup=impulsive_spending_kb())
        return
    await state.update_data(impulsive_spending=message.text)
    await state.set_state(OnboardingFSM.expense_tracking)
    await message.answer("Ведёте ли Вы учёт расходов?", reply_markup=expense_tracking_kb())


@router.message(OnboardingFSM.expense_tracking)
async def process_expense_tracking(message: Message, state: FSMContext):
    if message.text not in TRACKING:
        await message.answer("Пожалуйста, выберите один из вариантов.", reply_markup=expense_tracking_kb())
        return

    await state.update_data(expense_tracking=message.text)
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

    await message.answer(
        "✅ Диагностика завершена.\n\n"
        "Я сформировал Ваш финансовый профиль.\n\n"
        "Теперь Вы можете получить план расходов, проверить бюджет, "
        "рассчитать кредитные карты или задать вопрос финансовому консультанту.",
        reply_markup=open_menu_kb(),
    )
