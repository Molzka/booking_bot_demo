import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    bot_token: str
    admin_id: int
    database_url: str


def load_config() -> Config:
    load_dotenv()

    bot_token = os.getenv("BOT_TOKEN", "").strip()
    raw_admin_id = os.getenv("ADMIN_ID", "").strip()
    database_url = os.getenv("DATABASE_URL", "sqlite:///botbooking.sqlite3").strip()

    if not bot_token:
        raise RuntimeError("BOT_TOKEN is required in .env")
    if not raw_admin_id.isdigit():
        raise RuntimeError("ADMIN_ID must be a numeric Telegram user id")

    return Config(
        bot_token=bot_token,
        admin_id=int(raw_admin_id),
        database_url=database_url,
    )
