from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config.settings import BASE_DIR, get_settings
from app.models.database import Base

logger = logging.getLogger(__name__)

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _ensure_data_dir(url: str) -> None:
    if "sqlite" in url:
        raw_path = url.split("///")[-1]
        if not Path(raw_path).is_absolute():
            raw_path = str(BASE_DIR / raw_path)
        Path(raw_path).parent.mkdir(parents=True, exist_ok=True)


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        settings = get_settings()
        _ensure_data_dir(settings.database_url)
        _engine = create_async_engine(settings.database_url, echo=False)
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(), class_=AsyncSession, expire_on_commit=False
        )
    return _session_factory


async def _ensure_sqlite_columns(engine: AsyncEngine) -> None:
    """Añade columnas faltantes en SQLite (create_all no altera tablas existentes)."""
    settings = get_settings()
    if "sqlite" not in settings.database_url.lower():
        return
    async with engine.begin() as conn:
        r = await conn.execute(
            text(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name='classifications'"
            )
        )
        if r.fetchone() is None:
            return
        r2 = await conn.execute(text("PRAGMA table_info(classifications)"))
        columns = {row[1] for row in r2.fetchall()}
        if "decision_final" not in columns:
            await conn.execute(
                text("ALTER TABLE classifications ADD COLUMN decision_final VARCHAR(50)")
            )
            logger.info("SQLite: columna decision_final añadida (migración)")


async def init_db() -> None:
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await _ensure_sqlite_columns(engine)
    logger.info("Base de datos inicializada")


async def close_db() -> None:
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("Conexión a base de datos cerrada")
