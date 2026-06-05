import asyncio
import logging

from aiogram import Dispatcher
from app.database.fsm_storage import SQLiteFSMStorage
from app.middlewares.anti_abuse import MessageThrottlingMiddleware, CallbackThrottlingMiddleware
from app.services.typing_bot import TypingBot
from app.services.push_service import run_push_scheduler

from app.config import BOT_TOKEN
from app.database.db import init_db
from app.handlers import (
    start,
    onboarding,
    menu,
    reset,
    admin,
    consultation,
    budget_check,
    credit_cards,
    goals,
    expenses,
    rating,
    articles,
    personal_cabinet,
    payments,
    fallback,
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

    bot = TypingBot(token=BOT_TOKEN)
    dp = Dispatcher(storage=SQLiteFSMStorage())

    # Онбординг и сброс — без throttle, чтобы не мешать кликам по кнопкам
    dp.include_router(start.router)
    dp.include_router(admin.router)
    dp.include_router(reset.router)
    dp.include_router(onboarding.router)

    # Все остальные роутеры — с защитой от абуза
    throttle = MessageThrottlingMiddleware()
    cb_throttle = CallbackThrottlingMiddleware()

    for r in (menu.router, consultation.router, budget_check.router,
              credit_cards.router, goals.router, expenses.router,
              rating.router, articles.router, personal_cabinet.router,
              payments.router, fallback.router):
        r.message.middleware(throttle)

    for r in (articles.router, personal_cabinet.router, goals.router):
        r.callback_query.middleware(cb_throttle)

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
    dp.include_router(fallback.router)

    logger.info("Бот запускается...")
    asyncio.create_task(run_push_scheduler(bot))
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        logger.info("Бот остановлен")


if __name__ == "__main__":
    asyncio.run(main())
