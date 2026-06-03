from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from datetime import datetime

from app.database import db
from app.keyboards.reply import main_menu_kb

router = Router()


async def send_main_menu(message: Message, user: dict):
    profile = await db.get_user_profile(user["id"])
    score = profile.get("financial_score", 0) if profile else 0
    main_risk = profile.get("main_risk", "Не определен") if profile else "Не определен"

    tariff = user.get("tariff", "free")
    sub_until = user.get("subscription_until")

    if tariff == "premium" and sub_until:
        try:
            until_dt = datetime.fromisoformat(sub_until)
            if until_dt > datetime.utcnow():
                sub_status = f"💎 Премиум до {until_dt.strftime('%d.%m.%Y')}"
            else:
                sub_status = "🔓 Бесплатный"
        except Exception:
            sub_status = "🔓 Бесплатный"
    else:
        sub_status = "🔓 Бесплатный"

    text = (
        "💰 <b>Финансовый консультант AI</b>\n\n"
        "Помогаю понять, куда уходят деньги, пережить период до зарплаты "
        "и начать откладывать без жёсткой экономии.\n\n"
        f"📊 <b>Ваш финансовый профиль:</b>\n"
        f"Финансовая устойчивость: {score}/100\n"
        f"Основной риск: {main_risk}\n"
        f"Статус: {sub_status}\n\n"
        "Выберите раздел ниже."
    )
    await message.answer(text, reply_markup=main_menu_kb(), parse_mode="HTML")


@router.message(F.text == "📋 Открыть главное меню")
async def open_main_menu(message: Message, state: FSMContext):
    await state.clear()
    user = await db.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    await send_main_menu(message, user)


@router.message(F.text == "⬅️ Главное меню")
async def back_to_main_menu(message: Message, state: FSMContext):
    await state.clear()
    user = await db.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    await send_main_menu(message, user)
