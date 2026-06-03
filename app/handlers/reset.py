from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from app.database import db
from app.keyboards.reply import start_onboarding_kb, main_menu_kb

router = Router()


@router.message(Command("Сброс12"))
@router.message(F.text == "Сброс12")
async def reset_full_cmd(message: Message, state: FSMContext):
    """Полный сброс: FSM + все данные. Следующий /start — с нуля."""
    await state.clear()
    await db.reset_full(message.from_user.id)
    await message.answer(
        "🗑️ <b>Полный сброс выполнен.</b>\n\n"
        "Все данные удалены: профиль, история, цели, карты.\n"
        "Команда /start запустит бота с нуля.",
        parse_mode="HTML",
        reply_markup=start_onboarding_kb(),
    )


@router.message(Command("Сброс11"))
@router.message(F.text == "Сброс11")
async def reset_soft_cmd(message: Message, state: FSMContext):
    """Мягкий сброс: FSM очищается, онбординг считается пройденным. /start → главное меню."""
    await state.clear()
    await db.reset_soft(message.from_user.id)

    user = await db.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )

    from app.handlers.menu import send_main_menu
    await message.answer(
        "🔄 <b>Мягкий сброс выполнен.</b>\n\n"
        "Диалог очищен. Данные профиля сохранены.\n"
        "Открываю главное меню...",
        parse_mode="HTML",
    )
    await send_main_menu(message, user)
