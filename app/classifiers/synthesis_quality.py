"""Heurísticas para detectar redacción coloquial en síntesis de tarea (tests, CI, métricas).

No modifica respuestas del modelo en producción; sirve para asserts y revisiones automáticas.
"""

from __future__ import annotations

import unicodedata

# Subcadenas (sin acentos) que suelen indicar instrucción interpersonal en lugar de acto procesal.
_COLOQUIAL_JUDGE_MARKERS: tuple[str, ...] = (
    "dile al juez",
    "dile al magistrado",
    "dile al mp",
    "dile a la juez",
    "dile a la magistrada",
    "pidele al juez",
    "pidele al magistrado",
    "pidele a la juez",
    "pidele al mp",
    "hablale al juez",
    "hablale al magistrado",
    "hablale al mp",
    "hazle saber al juez",
    "hazle saber al magistrado",
    "cuentale al juez",
    "comentale al juez",
)


def _fold_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s.casefold())
        if unicodedata.category(c) != "Mn"
    )


def colloquial_judge_markers_in_task(tarea: str | None) -> tuple[str, ...]:
    """Devuelve marcadores coloquiales encontrados en la síntesis (vacío si ninguno)."""
    if not tarea or not tarea.strip():
        return ()
    folded = _fold_accents(tarea)
    found: list[str] = []
    for m in _COLOQUIAL_JUDGE_MARKERS:
        if m in folded:
            found.append(m)
    return tuple(found)


def task_synthesis_ok_for_escritos_presentados(tarea: str | None) -> bool:
    """True si la tarea no contiene marcadores coloquiales típicos hacia el juez."""
    return len(colloquial_judge_markers_in_task(tarea)) == 0
