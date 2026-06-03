from app.database import db


async def check_subscription(telegram_id: int) -> bool:
    return await db.is_subscription_active(telegram_id)
