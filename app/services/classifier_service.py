from __future__ import annotations

import logging
from dataclasses import dataclass

from app.catalog.loader import validate_classification
from app.classifiers.capa_1 import Capa1Result, classify_capa1
from app.classifiers.capa_2 import Capa2Result, classify_capa2
from app.classifiers.confidence import compute_combined_confidence
from app.storage.repository import save_classification

logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    capa1: Capa1Result
    capa2: Capa2Result | None
    combined_confidence: float
    catalog_valid: bool
    db_id: int


async def process_message(
    *,
    chat_id: int,
    message_id: int,
    text: str,
    equipo_primordial: str = "No especificado",
) -> ClassificationResult:
    logger.info("Procesando mensaje chat=%s msg=%s", chat_id, message_id)

    capa1 = await classify_capa1(text, equipo_primordial)
    logger.info(
        "Capa 1: positivo=%s equipo=%s confianza=%.2f",
        capa1.positivo, capa1.equipo_probable, capa1.confianza,
    )

    capa2: Capa2Result | None = None
    catalog_valid = False

    if capa1.positivo:
        capa2 = await classify_capa2(text, equipo_primordial)
        logger.info(
            "Capa 2: equipo=%s tabla=%s null=%s",
            capa2.equipo, capa2.tabla, capa2.is_null,
        )
        if not capa2.is_null:
            catalog_valid = validate_classification(capa2.equipo, capa2.tabla)
            if not catalog_valid:
                logger.warning(
                    "Capa 2 devolvió equipo/tabla no presente en catálogo: %s / %s",
                    capa2.equipo, capa2.tabla,
                )

    combined = compute_combined_confidence(
        capa1.confianza,
        capa2.is_null if capa2 else True,
    )

    record = await save_classification(
        telegram_chat_id=chat_id,
        telegram_message_id=message_id,
        raw_text=text,
        capa1_positivo=capa1.positivo,
        capa1_equipo=capa1.equipo_probable,
        capa1_tabla=capa1.tabla_probable,
        capa1_confianza=capa1.confianza,
        capa1_motivo=capa1.motivo,
        capa2_equipo=capa2.equipo if capa2 else None,
        capa2_tabla=capa2.tabla if capa2 else None,
        capa2_tarea=capa2.tarea if capa2 else None,
    )

    return ClassificationResult(
        capa1=capa1,
        capa2=capa2,
        combined_confidence=combined,
        catalog_valid=catalog_valid,
        db_id=record.id,
    )
