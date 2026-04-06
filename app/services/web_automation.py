"""
Placeholder para futura integración con Playwright.

Este módulo contendrá la lógica de automatización web para registrar
actividades en la página externa del despacho. No se implementa en el MVP
pero la estructura queda lista para extenderlo.

Dependencia futura: playwright
    pip install playwright
    playwright install chromium
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


async def register_task_in_external_system(
    equipo: str,
    tabla: str,
    tarea: str,
) -> bool:
    """
    Registra una tarea clasificada en el sistema externo vía automatización web.
    Por ahora solo loguea la intención; la implementación real usará Playwright.
    """
    logger.info(
        "TODO: Registrar tarea en sistema externo — equipo=%s tabla=%s tarea=%s",
        equipo, tabla, tarea,
    )
    return False
