from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

router = Router()


@router.message()
async def fallback_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        return

    await message.answer(
        "Не понял команду.\n\n"
        "Нажмите /start чтобы открыть бота, или /menu для главного меню."
    )
