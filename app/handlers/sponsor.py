import logging
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from app.database.settings import get_setting, set_setting
from app.keyboards.sponsor_kb import sponsor_gate_kb

logger = logging.getLogger(__name__)
router = Router()

ADMIN_ID = 1715461306

GATE_TEXT = (
    "Прежде чем начнем я хотел бы кое что сказать. "
    "Вероятно сложные жизненные обстоятельства привели вас ко мне. "
    "На протяжении 7 лет мои консультации получили уже более 8000 человек. "
    "Среди них финансовую грамотность обрел молодой парень и открыл свое дело, "
    "а после проинвестировал солидную сумму в создание данного бота. "
    "В знак благодарности я прошу оформить подписку на его канал "
    "и мы сразу приступим к первой бесплатной консультации"
)


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def is_sponsor_enabled() -> bool:
    return await get_setting("sponsor:enabled", "0") == "1"


async def get_sponsor_link() -> str:
    return await get_setting("sponsor:link", "")


async def get_sponsor_channel() -> str:
    return await get_setting("sponsor:channel", "")


async def is_subscribed(bot: Bot, user_id: int) -> bool:
    """Returns True if user is subscribed, or if gate is disabled / channel not set."""
    channel = await get_sponsor_channel()
    if not channel:
        return True
    try:
        member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception as e:
        logger.warning("Sponsor check failed for user %s: %s", user_id, e)
        return False  # fail-safe: treat as not subscribed


async def show_gate(target: Message | CallbackQuery, bot: Bot):
    """Send the sponsor gate plate."""
    link = await get_sponsor_link()
    kb = sponsor_gate_kb(link) if link else None
    text = GATE_TEXT

    if isinstance(target, CallbackQuery):
        await target.message.answer(text, reply_markup=kb)
    else:
        await target.answer(text, reply_markup=kb)


async def check_gate(message: Message, bot: Bot) -> bool:
    """
    Returns True if user may proceed (sponsor disabled OR already subscribed).
    Returns False and shows the gate if subscription required but missing.
    """
    if not await is_sponsor_enabled():
        return True
    if await is_subscribed(bot, message.from_user.id):
        return True
    await show_gate(message, bot)
    return False


# ─── Admin commands ────────────────────────────────────────────────────────────

@router.message(Command("link"))
async def cmd_link(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Использование: /link <url>")
        return
    url = parts[1].strip()
    await set_setting("sponsor:link", url)
    await message.answer(f"✅ Ссылка сохранена:\n{url}")


@router.message(Command("channel_id"))
async def cmd_channel_id(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Использование: /channel_id @username или -1001234567890")
        return
    channel = parts[1].strip()
    await set_setting("sponsor:channel", channel)
    await message.answer(f"✅ ID канала сохранён: {channel}")


@router.message(Command("sponsor"))
async def cmd_sponsor_toggle(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    current = await get_setting("sponsor:enabled", "0")
    new_val = "0" if current == "1" else "1"
    await set_setting("sponsor:enabled", new_val)
    status = "✅ ВКЛЮЧЕНА" if new_val == "1" else "❌ ВЫКЛЮЧЕНА"

    link    = await get_sponsor_link()
    channel = await get_sponsor_channel()
    await message.answer(
        f"Спонсорская плашка: {status}\n\n"
        f"Ссылка: {link or '—'}\n"
        f"Канал: {channel or '—'}"
    )


# ─── Sponsor check callback ────────────────────────────────────────────────────

@router.callback_query(F.data == "sponsor:check")
async def sponsor_check_callback(callback: CallbackQuery):
    bot = callback.bot
    if await is_subscribed(bot, callback.from_user.id):
        await callback.message.delete()
        from app.database.db import get_user
        from app.handlers.menu import send_main_menu
        user = await get_user(callback.from_user.id)
        if user:
            await send_main_menu(callback.message, user)
        await callback.answer("✅ Подписка подтверждена!")
    else:
        await callback.answer("Вы ещё не подписались на канал.", show_alert=True)


# Sponsor gate is enforced at two guaranteed entry points:
# 1. End of onboarding (onboarding.py)
# 2. send_main_menu() in menu.py — every section is accessed via main menu
# A catch-all handler cannot be used here because aiogram 3 treats
# any handler return as "handled" and stops further routing.
