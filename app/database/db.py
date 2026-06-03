import aiosqlite
import os
from datetime import datetime
from typing import Optional
from app.config import DB_PATH


async def get_db() -> aiosqlite.Connection:
    os.makedirs(os.path.dirname(DB_PATH) if os.path.dirname(DB_PATH) else ".", exist_ok=True)
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_db():
    os.makedirs("data", exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                onboarding_completed BOOLEAN DEFAULT FALSE,
                subscription_until TIMESTAMP,
                tariff TEXT DEFAULT 'free'
            );

            CREATE TABLE IF NOT EXISTS user_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL REFERENCES users(id),
                work_type TEXT,
                work_sphere TEXT,
                income_range TEXT,
                spending_style TEXT,
                financial_literacy TEXT,
                impulsive_spending TEXT,
                expense_tracking TEXT,
                debts_status TEXT,
                salary_end_status TEXT,
                money_before_salary TEXT,
                financial_score INTEGER DEFAULT 0,
                main_risk TEXT
            );

            CREATE TABLE IF NOT EXISTS consultations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                consultation_type TEXT NOT NULL,
                input_data TEXT NOT NULL,
                ai_response TEXT NOT NULL,
                is_paid BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                goal_name TEXT NOT NULL,
                target_amount REAL NOT NULL,
                monthly_saving REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS credit_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                card_name TEXT NOT NULL,
                debt_amount REAL NOT NULL,
                interest_rate REAL NOT NULL,
                min_payment REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                amount_stars INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        await db.commit()


async def get_or_create_user(telegram_id: int, username: Optional[str], first_name: Optional[str]) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
        ) as cursor:
            user = await cursor.fetchone()

        if not user:
            await db.execute(
                "INSERT INTO users (telegram_id, username, first_name) VALUES (?, ?, ?)",
                (telegram_id, username, first_name),
            )
            await db.commit()
            async with db.execute(
                "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
            ) as cursor:
                user = await cursor.fetchone()

        return dict(user)


async def get_user(telegram_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_user_profile(user_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM user_profiles WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def save_user_profile(user_id: int, data: dict):
    async with aiosqlite.connect(DB_PATH) as db:
        existing = None
        async with db.execute(
            "SELECT id FROM user_profiles WHERE user_id = ?", (user_id,)
        ) as cursor:
            existing = await cursor.fetchone()

        if existing:
            sets = ", ".join(f"{k} = ?" for k in data.keys())
            await db.execute(
                f"UPDATE user_profiles SET {sets} WHERE user_id = ?",
                (*data.values(), user_id),
            )
        else:
            cols = "user_id, " + ", ".join(data.keys())
            placeholders = "?, " + ", ".join("?" for _ in data)
            await db.execute(
                f"INSERT INTO user_profiles ({cols}) VALUES ({placeholders})",
                (user_id, *data.values()),
            )
        await db.commit()


async def mark_onboarding_complete(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET onboarding_completed = TRUE WHERE telegram_id = ?",
            (telegram_id,),
        )
        await db.commit()


async def save_consultation(user_id: int, consultation_type: str, input_data: str, ai_response: str, is_paid: bool = False):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO consultations (user_id, consultation_type, input_data, ai_response, is_paid) VALUES (?, ?, ?, ?, ?)",
            (user_id, consultation_type, input_data, ai_response, is_paid),
        )
        await db.commit()


async def get_consultations(user_id: int, limit: int = 10) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM consultations WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def count_free_consultations(user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM consultations WHERE user_id = ? AND is_paid = FALSE",
            (user_id,),
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


async def save_goal(user_id: int, goal_name: str, target_amount: float, monthly_saving: float) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO goals (user_id, goal_name, target_amount, monthly_saving) VALUES (?, ?, ?, ?)",
            (user_id, goal_name, target_amount, monthly_saving),
        )
        await db.commit()
        return cursor.lastrowid


async def get_goal(user_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM goals WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
            (user_id,),
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def save_credit_card(user_id: int, card_name: str, debt_amount: float, interest_rate: float, min_payment: float) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO credit_cards (user_id, card_name, debt_amount, interest_rate, min_payment) VALUES (?, ?, ?, ?, ?)",
            (user_id, card_name, debt_amount, interest_rate, min_payment),
        )
        await db.commit()
        return cursor.lastrowid


async def get_credit_cards(user_id: int) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM credit_cards WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def delete_credit_card(card_id: int, user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM credit_cards WHERE id = ? AND user_id = ?",
            (card_id, user_id),
        )
        await db.commit()


async def save_payment(user_id: int, amount_stars: int, product_name: str, status: str = "completed"):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO payments (user_id, amount_stars, product_name, status) VALUES (?, ?, ?, ?)",
            (user_id, amount_stars, product_name, status),
        )
        await db.commit()


async def activate_subscription(telegram_id: int, days: int):
    from datetime import timedelta
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT subscription_until FROM users WHERE telegram_id = ?", (telegram_id,)
        ) as cursor:
            row = await cursor.fetchone()

        now = datetime.utcnow()
        if row and row[0]:
            try:
                current_until = datetime.fromisoformat(row[0])
                base = current_until if current_until > now else now
            except Exception:
                base = now
        else:
            base = now

        new_until = base + timedelta(days=days)
        await db.execute(
            "UPDATE users SET subscription_until = ?, tariff = 'premium' WHERE telegram_id = ?",
            (new_until.isoformat(), telegram_id),
        )
        await db.commit()


async def is_subscription_active(telegram_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT subscription_until FROM users WHERE telegram_id = ?", (telegram_id,)
        ) as cursor:
            row = await cursor.fetchone()

    if not row or not row[0]:
        return False
    try:
        until = datetime.fromisoformat(row[0])
        return until > datetime.utcnow()
    except Exception:
        return False


async def get_budget_checks_count(user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM consultations WHERE user_id = ? AND consultation_type = 'budget_check'",
            (user_id,),
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


async def get_days_with_bot(user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT created_at FROM users WHERE id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
    if not row or not row[0]:
        return 0
    try:
        created = datetime.fromisoformat(row[0])
        return (datetime.utcnow() - created).days
    except Exception:
        return 0
