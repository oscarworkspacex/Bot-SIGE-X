from __future__ import annotations

import logging
from dataclasses import dataclass

from app.catalog.loader import validate_classification
from app.classifiers.capa_1 import Capa1Result, classify_capa1
from app.classifiers.capa_2 import Capa2Result, classify_capa2
from app.classifiers.confidence import compute_combined_confidence
from app.classifiers.prefilter import normalize_text, passes_prefilter
from app.storage.repository import save_classification

logger = logging.getLogger(__name__)


class Decision:
    PREFILTER_REJECTED = "prefilter_rejected"
    CAPA1_NEGATIVE = "capa1_negative"
    CAPA2_NULL = "capa2_null"
    TASK_FOUND = "task_found"
    TASK_INVALID_CATALOG = "task_invalid_catalog"
    ERROR = "error"


@dataclass
class ClassificationResult:
    capa1: Capa1Result | None
    capa2: Capa2Result | None
    catalog_valid: bool
    decision: str
    db_id: int | None
    confidence: float = 0.0


async def process_message(
    *,
    chat_id: int,
    message_id: int,
    text: str,
    equipo_primordial: str = "No especificado",
) -> ClassificationResult:
    normalized = normalize_text(text)
    logger.info("Procesando mensaje chat=%s msg=%s len=%d", chat_id, message_id, len(normalized))

    if not passes_prefilter(normalized):
        logger.info("Pre-filtro rechazó mensaje chat=%s msg=%s", chat_id, message_id)
        record = await save_classification(
            telegram_chat_id=chat_id,
            telegram_message_id=message_id,
            raw_text=text,
            decision_final=Decision.PREFILTER_REJECTED,
        )
        return ClassificationResult(
            capa1=None, capa2=None, catalog_valid=False,
            decision=Decision.PREFILTER_REJECTED, db_id=record.id,
        )

    capa1 = await classify_capa1(normalized, equipo_primordial)
    logger.info(
        "Capa 1: positivo=%s equipo=%s confianza=%.2f motivo=%s",
        capa1.positivo, capa1.equipo_probable, capa1.confianza, capa1.motivo,
    )

    if not capa1.positivo:
        record = await save_classification(
            telegram_chat_id=chat_id,
            telegram_message_id=message_id,
            raw_text=text,
            capa1_positivo=False,
            capa1_equipo=capa1.equipo_probable,
            capa1_tabla=capa1.tabla_probable,
            capa1_confianza=capa1.confianza,
            capa1_motivo=capa1.motivo,
            decision_final=Decision.CAPA1_NEGATIVE,
        )
        return ClassificationResult(
            capa1=capa1, capa2=None, catalog_valid=False,
            decision=Decision.CAPA1_NEGATIVE, db_id=record.id,
        )

    capa2 = await classify_capa2(normalized, equipo_primordial)
    logger.info(
        "Capa 2: equipo=%s tabla=%s tarea=%s null=%s",
        capa2.equipo, capa2.tabla, capa2.tarea, capa2.is_null,
    )

    combined_conf = compute_combined_confidence(capa1.confianza, capa2.is_null)

    if capa2.is_null:
        record = await save_classification(
            telegram_chat_id=chat_id,
            telegram_message_id=message_id,
            raw_text=text,
            capa1_positivo=True,
            capa1_equipo=capa1.equipo_probable,
            capa1_tabla=capa1.tabla_probable,
            capa1_confianza=capa1.confianza,
            capa1_motivo=capa1.motivo,
            decision_final=Decision.CAPA2_NULL,
        )
        return ClassificationResult(
            capa1=capa1, capa2=capa2, catalog_valid=False,
            decision=Decision.CAPA2_NULL, db_id=record.id,
            confidence=combined_conf,
        )

    catalog_valid = validate_classification(capa2.equipo, capa2.tabla)
    decision = Decision.TASK_FOUND if catalog_valid else Decision.TASK_INVALID_CATALOG

    if not catalog_valid:
        logger.warning(
            "Capa 2 devolvió equipo/tabla no presente en catálogo: %s / %s",
            capa2.equipo, capa2.tabla,
        )

    record = await save_classification(
        telegram_chat_id=chat_id,
        telegram_message_id=message_id,
        raw_text=text,
        capa1_positivo=True,
        capa1_equipo=capa1.equipo_probable,
        capa1_tabla=capa1.tabla_probable,
        capa1_confianza=capa1.confianza,
        capa1_motivo=capa1.motivo,
        capa2_equipo=capa2.equipo,
        capa2_tabla=capa2.tabla,
        capa2_tarea=capa2.tarea,
        decision_final=decision,
    )

    return ClassificationResult(
        capa1=capa1, capa2=capa2, catalog_valid=catalog_valid,
        decision=decision, db_id=record.id,
        confidence=combined_conf,
    )
