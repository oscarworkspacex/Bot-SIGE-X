from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_CATALOG_PATH = Path(__file__).parent / "catalog.json"

CatalogDict = dict[str, Any]


@lru_cache
def load_catalog() -> CatalogDict:
    with open(_CATALOG_PATH, encoding="utf-8") as f:
        return json.load(f)


def get_equipos() -> list[str]:
    return [eq["nombre"] for eq in load_catalog()["equipos"]]


def get_tablas_by_equipo(equipo: str) -> list[dict[str, Any]]:
    for eq in load_catalog()["equipos"]:
        if eq["nombre"] == equipo:
            return eq["tablas"]
    return []


def find_tabla(equipo: str, tabla_nombre: str) -> dict[str, Any] | None:
    for tabla in get_tablas_by_equipo(equipo):
        if tabla["nombre"] == tabla_nombre:
            return tabla
    return None


def validate_classification(equipo: str | None, tabla: str | None) -> bool:
    if not equipo or not tabla:
        return False
    return find_tabla(equipo, tabla) is not None
