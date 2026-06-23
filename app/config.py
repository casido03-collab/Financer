import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///data/finance_bot.db")
DB_PATH: str = "data/finance_bot.db"

ADMIN_IDS: set[int] = {1715461306, 7198897686}
