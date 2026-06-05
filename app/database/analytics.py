"""
All analytics queries for the admin panel.
"""
import aiosqlite
from datetime import datetime, timedelta
from typing import Optional
from app.config import DB_PATH

AI_COST_PER_REQUEST = 0.002  # USD estimate per OpenAI request


# ─── Migration helpers ────────────────────────────────────────────────────────

async def migrate_analytics():
    """Add analytics columns and events table if not present."""
    async with aiosqlite.connect(DB_PATH) as db:
        # New columns on users
        for col, definition in [
            ("last_seen_at",           "TIMESTAMP"),
            ("first_consultation_at",  "TIMESTAMP"),
            ("first_payment_at",       "TIMESTAMP"),
            ("last_opened_section",    "TEXT"),
            ("last_push_at",           "TIMESTAMP"),
            ("push_open_count",        "INTEGER DEFAULT 0"),
            ("total_consultations",    "INTEGER DEFAULT 0"),
            ("total_budget_checks",    "INTEGER DEFAULT 0"),
            ("total_calculator_uses",  "INTEGER DEFAULT 0"),
        ]:
            try:
                await db.execute(f"ALTER TABLE users ADD COLUMN {col} {definition}")
            except Exception:
                pass  # column already exists

        # Events table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL REFERENCES users(id),
                event_type TEXT NOT NULL,
                payload    TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Push log table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS push_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id),
                push_type   TEXT NOT NULL,
                sent_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                opened      BOOLEAN DEFAULT FALSE
            )
        """)
        await db.commit()


# ─── Event tracking ───────────────────────────────────────────────────────────

async def track_event(user_id: int, event_type: str, payload: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO events (user_id, event_type, payload) VALUES (?, ?, ?)",
            (user_id, event_type, payload),
        )
        await db.commit()


async def touch_user(telegram_id: int):
    """Update last_seen_at for user."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET last_seen_at = ? WHERE telegram_id = ?",
            (datetime.utcnow().isoformat(), telegram_id),
        )
        await db.commit()


async def record_consultation(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE users
            SET total_consultations = total_consultations + 1,
                first_consultation_at = COALESCE(first_consultation_at, ?)
            WHERE id = ?
        """, (datetime.utcnow().isoformat(), user_id))
        await db.commit()


async def record_payment(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE users
            SET first_payment_at = COALESCE(first_payment_at, ?)
            WHERE id = ?
        """, (datetime.utcnow().isoformat(), user_id))
        await db.commit()


async def record_section(user_id: int, section: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET last_opened_section = ? WHERE id = ?",
            (section, user_id),
        )
        await db.commit()
    await track_event(user_id, "section_open", section)


async def record_budget_check(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET total_budget_checks = total_budget_checks + 1 WHERE id = ?",
            (user_id,),
        )
        await db.commit()


async def record_calculator_use(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET total_calculator_uses = total_calculator_uses + 1 WHERE id = ?",
            (user_id,),
        )
        await db.commit()


async def record_ai_request(user_id: int):
    await track_event(user_id, "ai_request")


# ─── Analytics queries ────────────────────────────────────────────────────────

def _today() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")

def _days_ago(n: int) -> str:
    return (datetime.utcnow() - timedelta(days=n)).strftime("%Y-%m-%d")


async def get_users_stats() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        async def count(where: str, params=()):
            async with db.execute(f"SELECT COUNT(*) FROM users {where}", params) as c:
                r = await c.fetchone()
                return r[0] if r else 0

        total   = await count("")
        today   = await count("WHERE DATE(created_at) = ?", (_today(),))
        yesterday = await count("WHERE DATE(created_at) = ?", (_days_ago(1),))
        week    = await count("WHERE DATE(created_at) >= ?", (_days_ago(7),))
        month   = await count("WHERE DATE(created_at) >= ?", (_days_ago(30),))

    return {"total": total, "today": today, "yesterday": yesterday, "week": week, "month": month}


async def get_active_users() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        async def dau(days_ago: int):
            async with db.execute(
                "SELECT COUNT(DISTINCT user_id) FROM events WHERE DATE(created_at) >= ?",
                (_days_ago(days_ago),)
            ) as c:
                r = await c.fetchone()
                return r[0] if r else 0

        dau_val = await dau(0)
        wau_val = await dau(7)
        mau_val = await dau(30)
    return {"dau": dau_val, "wau": wau_val, "mau": mau_val}


async def get_retention() -> dict:
    """
    DX = share of users (registered X+ days ago) who returned within X days.
    """
    result = {}
    async with aiosqlite.connect(DB_PATH) as db:
        for label, reg_days, ret_days in [
            ("D1",  1,  1),
            ("D3",  3,  3),
            ("D7",  7,  7),
            ("D14", 14, 14),
            ("D30", 30, 30),
        ]:
            async with db.execute(
                "SELECT COUNT(*) FROM users WHERE DATE(created_at) <= ?",
                (_days_ago(reg_days),)
            ) as c:
                base = (await c.fetchone())[0] or 0

            if base == 0:
                result[label] = 0
                continue

            sql = f"""
                SELECT COUNT(DISTINCT u.id)
                FROM users u
                JOIN events e ON e.user_id = u.id
                WHERE DATE(u.created_at) <= ?
                  AND DATE(e.created_at) BETWEEN DATE(u.created_at, '+1 day')
                      AND DATE(u.created_at, '+{ret_days} days')
            """
            async with db.execute(sql, (_days_ago(reg_days),)) as c:
                came_back = (await c.fetchone())[0] or 0

            result[label] = round(came_back / base * 100, 1)

    return result


async def get_onboarding_funnel() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        async def cnt(where, params=()):
            async with db.execute(f"SELECT COUNT(*) FROM users {where}", params) as c:
                return (await c.fetchone())[0] or 0

        async def ev(event_type):
            async with db.execute(
                "SELECT COUNT(DISTINCT user_id) FROM events WHERE event_type = ?",
                (event_type,)
            ) as c:
                return (await c.fetchone())[0] or 0

        started     = await cnt("")
        began_diag  = await ev("onboarding_start")
        completed   = await cnt("WHERE onboarding_completed = TRUE")
        opened_menu = await ev("section_open")
        consulted   = await cnt("WHERE total_consultations > 0")
        paid        = await cnt("WHERE first_payment_at IS NOT NULL")

    return {
        "started":     started,
        "began_diag":  began_diag,
        "completed":   completed,
        "opened_menu": opened_menu,
        "consulted":   consulted,
        "paid":        paid,
    }


async def get_sections_stats() -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT payload, COUNT(*) as cnt
            FROM events
            WHERE event_type = 'section_open' AND payload IS NOT NULL
            GROUP BY payload
            ORDER BY cnt DESC
            LIMIT 10
        """) as c:
            rows = await c.fetchall()
    return [{"section": r[0], "count": r[1]} for r in rows]


async def get_sales_funnel() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        async def cnt(where, params=()):
            async with db.execute(f"SELECT COUNT(*) FROM users {where}", params) as c:
                return (await c.fetchone())[0] or 0
        async def ev(event_type):
            async with db.execute(
                "SELECT COUNT(DISTINCT user_id) FROM events WHERE event_type = ?",
                (event_type,)
            ) as c:
                return (await c.fetchone())[0] or 0

        got_free_plan = await cnt("WHERE total_consultations > 0")
        saw_offer     = await ev("upsell_shown")
        tapped_pay    = await ev("payment_initiated")
        paid          = await cnt("WHERE first_payment_at IS NOT NULL")

    conversion = round(paid / got_free_plan * 100, 1) if got_free_plan else 0
    return {
        "got_free_plan": got_free_plan,
        "saw_offer":     saw_offer,
        "tapped_pay":    tapped_pay,
        "paid":          paid,
        "conversion":    conversion,
    }


async def get_revenue() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        async def stars(where, params=()):
            async with db.execute(
                f"SELECT COALESCE(SUM(amount_stars), 0) FROM payments WHERE status='completed' {where}",
                params
            ) as c:
                return (await c.fetchone())[0] or 0

        today  = await stars("AND DATE(created_at) = ?", (_today(),))
        yday   = await stars("AND DATE(created_at) = ?", (_days_ago(1),))
        week   = await stars("AND DATE(created_at) >= ?", (_days_ago(7),))
        month  = await stars("AND DATE(created_at) >= ?", (_days_ago(30),))

        async with db.execute(
            "SELECT COUNT(*) FROM payments WHERE status='completed'"
        ) as c:
            total_orders = (await c.fetchone())[0] or 0

    avg_check = round(month / total_orders) if total_orders else 200
    return {"today": today, "yesterday": yday, "week": week, "month": month, "avg_check": avg_check}


async def get_ai_stats() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM events WHERE event_type = 'ai_request'"
        ) as c:
            total_requests = (await c.fetchone())[0] or 0

        async with db.execute(
            "SELECT COALESCE(SUM(amount_stars), 0) FROM payments WHERE status='completed'"
        ) as c:
            total_stars = (await c.fetchone())[0] or 0

    total_cost = round(total_requests * AI_COST_PER_REQUEST, 2)
    avg_cost   = round(AI_COST_PER_REQUEST, 4)
    revenue_usd = total_stars * 0.013  # ~$0.013 per star
    margin = round((1 - total_cost / revenue_usd) * 100, 1) if revenue_usd > 0 else 100.0

    return {
        "requests":    total_requests,
        "total_cost":  total_cost,
        "avg_cost":    avg_cost,
        "total_stars": total_stars,
        "margin":      margin,
    }


async def get_push_stats() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM push_log") as c:
            sent = (await c.fetchone())[0] or 0
        async with db.execute("SELECT COUNT(*) FROM push_log WHERE opened = TRUE") as c:
            opened = (await c.fetchone())[0] or 0
        async with db.execute("""
            SELECT push_type, COUNT(*) as total,
                   SUM(CASE WHEN opened THEN 1 ELSE 0 END) as opens
            FROM push_log
            GROUP BY push_type
            ORDER BY opens DESC
            LIMIT 5
        """) as c:
            rows = await c.fetchall()

    ctr = round(opened / sent * 100, 1) if sent else 0
    top = [{"type": r[0], "total": r[1], "opens": r[2],
            "ctr": round(r[2] / r[1] * 100, 1) if r[1] else 0} for r in rows]
    return {"sent": sent, "opened": opened, "ctr": ctr, "top": top}


async def get_articles_stats() -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT payload, COUNT(*) as cnt
            FROM events
            WHERE event_type = 'article_view' AND payload IS NOT NULL
            GROUP BY payload
            ORDER BY cnt DESC
            LIMIT 5
        """) as c:
            rows = await c.fetchall()
    return [{"article": r[0], "count": r[1]} for r in rows]


async def get_audience_stats() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM user_profiles") as c:
            total = (await c.fetchone())[0] or 1

        async def pct(col, val):
            async with db.execute(
                f"SELECT COUNT(*) FROM user_profiles WHERE {col} = ?", (val,)
            ) as c:
                n = (await c.fetchone())[0] or 0
            return round(n / total * 100)

        # Work types
        async with db.execute("""
            SELECT work_type, COUNT(*) as cnt FROM user_profiles
            WHERE work_type IS NOT NULL
            GROUP BY work_type ORDER BY cnt DESC LIMIT 3
        """) as c:
            work_types = await c.fetchall()

        no_tracking = await pct("expense_tracking", "Нет")
        impulsive    = await pct("impulsive_spending", "Да, это моя главная проблема")
        overspend    = await pct("spending_style", "Почти не контролирую расходы")

    return {
        "total":       total,
        "work_types":  [{"type": r[0], "count": r[1]} for r in work_types],
        "no_tracking": no_tracking,
        "impulsive":   impulsive,
        "overspend":   overspend,
    }
