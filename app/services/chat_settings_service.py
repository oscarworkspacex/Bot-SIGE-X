from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.catalog.loader import get_equipos
from app.models.database import ChatSettings
from app.storage.engine import get_session_factory

logger = logging.getLogger(__name__)

VALID_EQUIPOS: list[str] = get_equipos()

_EQUIPOS_LOWER: dict[str, str] = {e.lower(): e for e in VALID_EQUIPOS}


def normalize_equipo(raw: str) -> str | None:
    """Devuelve el nombre canónico del equipo o None si no es válido."""
    return _EQUIPOS_LOWER.get(raw.strip().lower())


async def get_equipo_principal(chat_id: int) -> str | None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        stmt = select(ChatSettings).where(ChatSettings.chat_id == chat_id)
        result = await session.execute(stmt)
        row = result.scalar_one_or_none()
        return row.equipo_principal if row else None


async def set_equipo_principal(chat_id: int, equipo: str) -> None:
    session_factory = get_session_factory()
    now = datetime.now(timezone.utc)
    async with session_factory() as session:
        stmt = select(ChatSettings).where(ChatSettings.chat_id == chat_id)
        result = await session.execute(stmt)
        row = result.scalar_one_or_none()
        if row:
            row.equipo_principal = equipo
            row.updated_at = now
        else:
            row = ChatSettings(
                chat_id=chat_id,
                equipo_principal=equipo,
                created_at=now,
                updated_at=now,
            )
            session.add(row)
        await session.commit()


async def clear_equipo_principal(chat_id: int) -> bool:
    """Elimina el equipo principal. Devuelve True si existía, False si no."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        stmt = select(ChatSettings).where(ChatSettings.chat_id == chat_id)
        result = await session.execute(stmt)
        row = result.scalar_one_or_none()
        if not row or row.equipo_principal is None:
            return False
        row.equipo_principal = None
        row.updated_at = datetime.now(timezone.utc)
        await session.commit()
        return True
