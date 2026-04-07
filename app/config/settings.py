from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
    )

    telegram_bot_token: str
    openai_api_key: str
    openai_model_capa1: str = "gpt-4o-mini"
    openai_model_capa2: str = "gpt-4o"
    openai_timeout: float = 30.0
    database_url: str = f"sqlite+aiosqlite:///{(BASE_DIR / 'data' / 'bot.db').as_posix()}"
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()


def setup_logging(level: str | None = None) -> None:
    log_level = level or get_settings().log_level
    logging.basicConfig(
        format="%(asctime)s | %(name)-25s | %(levelname)-7s | %(message)s",
        level=getattr(logging, log_level.upper(), logging.INFO),
    )
