from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from app.database import db
from app.keyboards.reply import start_onboarding_kb, main_menu_kb
from app.handlers.menu import send_main_menu

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = await db.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )

    if user.get("onboarding_completed"):
        await send_main_menu(message, user)
        return

    await message.answer(
        "👋 Привет.\n\n"
        "Я — Ваш ИИ финансовый эксперт.\n\n"
        "Помогу понять, куда уходят деньги, как дожить до зарплаты без долгов "
        "и как начать откладывать даже при обычном доходе.\n\n"
        "Сейчас я задам несколько вопросов. Ответы важны для формирования "
        "личного финансового плана и выхода из ситуации, когда денег не хватает до зарплаты.\n\n"
        "Это займет 2 минуты.",
        reply_markup=start_onboarding_kb(),
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext):
    await state.clear()
    user = await db.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    await send_main_menu(message, user)


@router.message(Command("profile"))
async def cmd_profile(message: Message, state: FSMContext):
    await state.clear()
    from app.services.user_profile import build_profile_text
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Сначала запустите бота командой /start")
        return
    text = await build_profile_text(user)
    await message.answer(text, parse_mode="HTML")
