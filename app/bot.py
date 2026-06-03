import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import BOT_TOKEN
from app.database.db import init_db
from app.handlers import (
    start,
    onboarding,
    menu,
    consultation,
    budget_check,
    credit_cards,
    goals,
    expenses,
    rating,
    articles,
    personal_cabinet,
    payments,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN не задан в .env файле")

    await init_db()
    logger.info("База данных инициализирована")

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start.router)
    dp.include_router(onboarding.router)
    dp.include_router(menu.router)
    dp.include_router(payments.router)
    dp.include_router(consultation.router)
    dp.include_router(budget_check.router)
    dp.include_router(credit_cards.router)
    dp.include_router(goals.router)
    dp.include_router(expenses.router)
    dp.include_router(rating.router)
    dp.include_router(articles.router)
    dp.include_router(personal_cabinet.router)

    logger.info("Бот запускается...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        logger.info("Бот остановлен")


if __name__ == "__main__":
    asyncio.run(main())
