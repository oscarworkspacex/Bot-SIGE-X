from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.models.database import Classification
from app.storage.engine import get_session_factory

logger = logging.getLogger(__name__)


async def save_classification(
    *,
    telegram_chat_id: int,
    telegram_message_id: int,
    raw_text: str,
    capa1_positivo: bool | None = None,
    capa1_equipo: str | None = None,
    capa1_tabla: str | None = None,
    capa1_confianza: float | None = None,
    capa1_motivo: str | None = None,
    capa2_equipo: str | None = None,
    capa2_tabla: str | None = None,
    capa2_tarea: str | None = None,
) -> Classification:
    session_factory = get_session_factory()
    async with session_factory() as session:
        record = Classification(
            telegram_chat_id=telegram_chat_id,
            telegram_message_id=telegram_message_id,
            raw_text=raw_text,
            capa1_positivo=capa1_positivo,
            capa1_equipo=capa1_equipo,
            capa1_tabla=capa1_tabla,
            capa1_confianza=capa1_confianza,
            capa1_motivo=capa1_motivo,
            capa2_equipo=capa2_equipo,
            capa2_tabla=capa2_tabla,
            capa2_tarea=capa2_tarea,
            created_at=datetime.now(timezone.utc),
        )
        session.add(record)
        await session.commit()
        await session.refresh(record)
        logger.info("Clasificación guardada: id=%s chat=%s", record.id, record.telegram_chat_id)
        return record


async def get_classifications_by_chat(chat_id: int, limit: int = 50) -> list[Classification]:
    session_factory = get_session_factory()
    async with session_factory() as session:
        stmt = (
            select(Classification)
            .where(Classification.telegram_chat_id == chat_id)
            .order_by(Classification.created_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
