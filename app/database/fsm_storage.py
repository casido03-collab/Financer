import json
import aiosqlite
from typing import Any, Dict, Optional
from aiogram.fsm.storage.base import BaseStorage, StorageKey, StateType

from app.config import DB_PATH


class SQLiteFSMStorage(BaseStorage):
    """FSM storage backed by SQLite — survives bot restarts."""

    async def _init(self):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS fsm_states (
                    key   TEXT PRIMARY KEY,
                    state TEXT,
                    data  TEXT NOT NULL DEFAULT '{}'
                )
            """)
            await db.commit()

    def _key(self, key: StorageKey) -> str:
        return f"{key.bot_id}:{key.chat_id}:{key.user_id}"

    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        await self._init()
        k = self._key(key)
        state_str = str(state) if state is not None else None
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                """
                INSERT INTO fsm_states (key, state) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET state = excluded.state
                """,
                (k, state_str),
            )
            await db.commit()

    async def get_state(self, key: StorageKey) -> Optional[str]:
        await self._init()
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT state FROM fsm_states WHERE key = ?", (self._key(key),)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None

    async def set_data(self, key: StorageKey, data: Dict[str, Any]) -> None:
        await self._init()
        k = self._key(key)
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                """
                INSERT INTO fsm_states (key, data) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET data = excluded.data
                """,
                (k, json.dumps(data, ensure_ascii=False)),
            )
            await db.commit()

    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        await self._init()
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT data FROM fsm_states WHERE key = ?", (self._key(key),)
            ) as cursor:
                row = await cursor.fetchone()
                return json.loads(row[0]) if row and row[0] else {}

    async def close(self) -> None:
        pass
