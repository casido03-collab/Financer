"""
Financial companion push notification system.
Rules:
- Max 1 push per user per 24 hours
- Priority: seg1 > seg2 > seg3 > seg4 > seg5 > seg6 > seg7
- Personalized where possible
- Stop after sequence exhausted
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

import aiosqlite

from app.config import DB_PATH
from app.texts.push_messages import (
    SEG1_TIMED, SEG2, SEG3, SEG4, SEG5, SEG6, SEG7,
)

logger = logging.getLogger(__name__)

PUSH_HOUR_START = 8   # UTC = 11 Moscow
PUSH_HOUR_END   = 19  # UTC = 22 Moscow


# ─── DB helpers ───────────────────────────────────────────────────────────────

async def _migrate_push_fields():
    async with aiosqlite.connect(DB_PATH) as db:
        for col, defn in [
            ("push_segment",     "INTEGER DEFAULT 0"),
            ("push_day_counter", "INTEGER DEFAULT 0"),
            ("last_push_type",   "TEXT"),
        ]:
            try:
                await db.execute(f"ALTER TABLE users ADD COLUMN {col} {defn}")
            except Exception:
                pass
        await db.commit()


async def _get_eligible_users() -> list:
    cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT u.*, up.work_type, up.work_sphere, up.spending_style
            FROM users u
            LEFT JOIN user_profiles up ON up.user_id = u.id
            WHERE (u.last_push_at IS NULL OR u.last_push_at < ?)
        """, (cutoff,)) as c:
            return [dict(r) for r in await c.fetchall()]


async def _mark_push_sent(user_id: int, segment: int, day: int, push_type: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE users
            SET last_push_at = ?, push_segment = ?, push_day_counter = ?, last_push_type = ?
            WHERE id = ?
        """, (datetime.utcnow().isoformat(), segment, day + 1, push_type, user_id))
        # also log it
        await db.execute("""
            INSERT INTO push_log (user_id, push_type) VALUES (?, ?)
        """, (user_id, push_type))
        await db.commit()


async def _get_last_budget_check(user_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT input_data FROM consultations
            WHERE user_id = ? AND consultation_type = 'budget_check'
            ORDER BY created_at DESC LIMIT 1
        """, (user_id,)) as c:
            row = await c.fetchone()
    return dict(row) if row else None


async def _get_user_goal(user_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT goal_name, target_amount, monthly_saving FROM goals
            WHERE user_id = ? ORDER BY created_at DESC LIMIT 1
        """, (user_id,)) as c:
            row = await c.fetchone()
    return dict(row) if row else None


async def _has_used_section(user_id: int, section: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT 1 FROM events
            WHERE user_id = ? AND event_type = 'section_open' AND payload = ?
            LIMIT 1
        """, (user_id, section)) as c:
            return bool(await c.fetchone())


async def _has_used_calculator(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT 1 FROM events
            WHERE user_id = ? AND event_type IN ('section_open')
            AND payload IN ('💳 Кредитные карты', '🧮 Калькулятор')
            LIMIT 1
        """, (user_id,)) as c:
            return bool(await c.fetchone())


async def _has_read_articles(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT 1 FROM events WHERE user_id = ? AND event_type = 'article_view' LIMIT 1
        """, (user_id,)) as c:
            return bool(await c.fetchone())


async def _onboarding_start_time(user_id: int) -> Optional[datetime]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT created_at FROM events
            WHERE user_id = ? AND event_type = 'onboarding_start'
            ORDER BY created_at ASC LIMIT 1
        """, (user_id,)) as c:
            row = await c.fetchone()
    if not row:
        return None
    try:
        return datetime.fromisoformat(row[0])
    except Exception:
        return None


# ─── Segment determination ────────────────────────────────────────────────────

async def _determine_segment(user: dict) -> Optional[tuple[int, int, str]]:
    """
    Returns (segment, day_index, message) or None if no push needed.
    """
    uid = user["id"]
    now = datetime.utcnow()

    # ── Segment 1: incomplete onboarding ──────────────────────────────────────
    if not user.get("onboarding_completed"):
        start = await _onboarding_start_time(uid)
        if start:
            elapsed = now - start
            last_type = user.get("last_push_type", "")

            if elapsed >= timedelta(days=7) and last_type != "seg1_7d":
                return 1, 3, SEG1_TIMED["7d"]
            if elapsed >= timedelta(days=3) and last_type not in ("seg1_3d", "seg1_7d"):
                return 1, 2, SEG1_TIMED["3d"]
            if elapsed >= timedelta(hours=24) and last_type not in ("seg1_24h", "seg1_3d", "seg1_7d"):
                return 1, 1, SEG1_TIMED["24h"]
            if elapsed >= timedelta(minutes=30) and last_type not in ("seg1_30min", "seg1_24h", "seg1_3d", "seg1_7d"):
                return 1, 0, SEG1_TIMED["30min"]
        return None  # no start event or too early

    # ── Segments 3-7 based on last activity ───────────────────────────────────
    last_section = user.get("last_opened_section", "")
    day = user.get("push_day_counter") or 0

    # Segment 3: budget check user
    if "Проверка бюджета" in (last_section or "") or user.get("total_budget_checks", 0) > 0:
        if day < len(SEG3):
            bc = await _get_last_budget_check(uid)
            msg = SEG3[day]
            # personalize if we have budget data
            if bc and day == 0:
                input_data = bc.get("input_data", "")
                if "Остаток:" in input_data:
                    try:
                        parts = input_data.split(",")
                        amount = parts[0].split(":")[1].strip().replace("₽", "").strip()
                        days_part = parts[1].split(":")[1].strip()
                        daily = round(float(amount) / int(days_part))
                        msg = (
                            f"📊 Вчера Ваш рекомендуемый лимит составлял {daily:,} ₽ в день.\n\n"
                            f"Проверим, удаётся ли его соблюдать?"
                        )
                    except Exception:
                        pass
            return 3, day, msg

    # Segment 4: consultation user
    if "Консультация" in (last_section or "") or (user.get("total_consultations") or 0) > 0:
        if day < len(SEG4):
            return 4, day, SEG4[day]

    # Segment 5: goal user
    goal = await _get_user_goal(uid)
    if goal and ("Моя цель" in (last_section or "") or goal):
        if day < len(SEG5):
            msg = SEG5[day]
            if day % 3 == 0:  # personalize every 3rd push
                msg = (
                    f"🎯 Напоминаю о Вашей цели: {goal['goal_name']} — "
                    f"{goal['target_amount']:,.0f} ₽.\n\n"
                    + msg.split("\n\n", 1)[-1] if "\n\n" in msg else msg
                )
            return 5, day, msg

    # Segment 6: credit card user
    if await _has_used_calculator(uid):
        if day < len(SEG6):
            return 6, day, SEG6[day]

    # Segment 7: article reader
    if await _has_read_articles(uid):
        if day < len(SEG7):
            return 7, day, SEG7[day]

    # Segment 2: onboarding done, never used anything
    if day < len(SEG2):
        return 2, day, SEG2[day]

    return None


# ─── Main push runner ─────────────────────────────────────────────────────────

async def send_daily_pushes(bot):
    """Called by the scheduler. Sends pushes to all eligible users."""
    now_utc = datetime.utcnow()
    if not (PUSH_HOUR_START <= now_utc.hour < PUSH_HOUR_END):
        return  # outside sending window

    await _migrate_push_fields()
    users = await _get_eligible_users()
    sent = 0

    for user in users:
        try:
            result = await _determine_segment(user)
            if not result:
                continue

            segment, day, message = result

            seg_type_map = {
                1: f"seg1_{['30min','24h','3d','7d'][min(day,3)]}",
                2: f"seg2_d{day}",
                3: f"seg3_d{day}",
                4: f"seg4_d{day}",
                5: f"seg5_d{day}",
                6: f"seg6_d{day}",
                7: f"seg7_d{day}",
            }
            push_type = seg_type_map.get(segment, f"seg{segment}_d{day}")

            await bot.send_message(
                chat_id=user["telegram_id"],
                text=message,
            )
            await _mark_push_sent(user["id"], segment, day, push_type)
            sent += 1
            await asyncio.sleep(0.05)  # rate limit: 20 msg/sec

        except Exception as e:
            logger.warning("Push failed for user %s: %s", user.get("telegram_id"), e)

    if sent:
        logger.info("Push run complete: %d messages sent", sent)


async def run_push_scheduler(bot):
    """Background asyncio task — runs every 30 minutes."""
    await asyncio.sleep(60)  # wait for bot to fully start
    await _migrate_push_fields()
    logger.info("Push scheduler started")

    while True:
        try:
            await send_daily_pushes(bot)
        except Exception as e:
            logger.error("Push scheduler error: %s", e)
        await asyncio.sleep(30 * 60)  # every 30 minutes
