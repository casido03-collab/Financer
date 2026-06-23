import logging
from typing import Any, Awaitable, Callable, Dict
from aiogram import Router, F, Bot, BaseMiddleware
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.database.settings import get_setting, set_setting
from app.keyboards.sponsor_kb import sponsor_gate_kb
from app.config import ADMIN_IDS

logger = logging.getLogger(__name__)
router = Router()

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
    if message.from_user.id in ADMIN_IDS:
        return True
    if await is_subscribed(bot, message.from_user.id):
        return True
    await show_gate(message, bot)
    return False


# ─── Admin commands ────────────────────────────────────────────────────────────

@router.message(Command("link"))
async def cmd_link(message: Message):
    if message.from_user.id not in ADMIN_IDS:
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
    if message.from_user.id not in ADMIN_IDS:
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
    if message.from_user.id not in ADMIN_IDS:
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


class SponsorMiddleware(BaseMiddleware):
    """
    Applied to all section routers.
    If sponsor gate is active and user is not subscribed:
      - Passes through if user is in an active FSM state (don't interrupt dialogs)
      - Shows gate and blocks otherwise
    """

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        # Only intercept Message events
        if not isinstance(event, Message):
            return await handler(event, data)

        # If sponsor disabled — pass through immediately
        if not await is_sponsor_enabled():
            return await handler(event, data)

        # If user is in an active FSM dialog — don't interrupt
        fsm: FSMContext = data.get("state")
        if fsm:
            current = await fsm.get_state()
            if current is not None:
                return await handler(event, data)

        # Skip commands (/, /start, /admin etc.)
        if event.text and event.text.startswith("/"):
            return await handler(event, data)

        # Admin bypass — never show gate to admin
        if event.from_user.id in ADMIN_IDS:
            return await handler(event, data)

        # Check subscription
        if await is_subscribed(event.bot, event.from_user.id):
            return await handler(event, data)

        # Not subscribed → show gate, block handler
        await show_gate(event, event.bot)
        return  # handler is NOT called
