"""Serialización del catálogo para prompts (una sola fuente: catalog.json)."""

from __future__ import annotations

import json
from typing import Any

from app.catalog.loader import load_catalog


def _tabla_for_prompt(tabla: dict[str, Any]) -> dict[str, Any]:
    return {
        "nombre": tabla["nombre"],
        "descripcion_general": tabla.get("descripcion", ""),
        "ejemplos": tabla.get("ejemplos") or [],
        "exclusiones": tabla.get("exclusiones") or [],
    }


def build_capa2_catalog_payload() -> dict[str, Any]:
    """Estructura alineada con el antiguo JSON embebido en capa_2 (descripcion_general)."""
    catalog = load_catalog()
    equipos_out: list[dict[str, Any]] = []
    for eq in catalog["equipos"]:
        equipos_out.append({
            "nombre": eq["nombre"],
            "tablas": [_tabla_for_prompt(t) for t in eq["tablas"]],
        })
    return {"equipos": equipos_out}


def build_capa2_catalog_json_text() -> str:
    return json.dumps(build_capa2_catalog_payload(), ensure_ascii=False, indent=2)
