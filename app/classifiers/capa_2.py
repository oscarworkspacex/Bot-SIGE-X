from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from openai import AsyncOpenAI

from app.catalog.loader import load_catalog, validate_classification
from app.config.settings import get_settings

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "capa_2.txt"
_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=get_settings().openai_api_key)
    return _client


@dataclass
class Capa2Result:
    tarea: str | None
    equipo: str | None
    tabla: str | None
    is_null: bool


@lru_cache
def _build_schema() -> dict:
    catalog = load_catalog()
    valid_equipos = [eq["nombre"] for eq in catalog["equipos"]]
    valid_tablas = sorted({
        tabla["nombre"]
        for eq in catalog["equipos"]
        for tabla in eq["tablas"]
    })

    return {
        "type": "object",
        "properties": {
            "tarea": {
                "anyOf": [{"type": "string"}, {"type": "null"}],
            },
            "equipo": {
                "anyOf": [
                    {"type": "string", "enum": valid_equipos},
                    {"type": "null"},
                ],
            },
            "tabla": {
                "anyOf": [
                    {"type": "string", "enum": valid_tablas},
                    {"type": "null"},
                ],
            },
        },
        "required": ["tarea", "equipo", "tabla"],
        "additionalProperties": False,
    }


def _build_catalog_json() -> str:
    catalog = load_catalog()
    compact = {"equipos": []}
    for equipo in catalog["equipos"]:
        eq = {"nombre": equipo["nombre"], "tablas": []}
        for tabla in equipo["tablas"]:
            t: dict = {"nombre": tabla["nombre"], "descripcion": tabla["descripcion"]}
            if tabla.get("ejemplos"):
                t["ejemplos"] = tabla["ejemplos"]
            if tabla.get("exclusiones"):
                t["exclusiones"] = tabla["exclusiones"]
            eq["tablas"].append(t)
        compact["equipos"].append(eq)
    return json.dumps(compact, ensure_ascii=False, indent=1)


def _build_criterios() -> str:
    catalog = load_catalog()
    criterios = catalog.get("criterios_desambiguacion", [])
    return "\n".join(f"- {c}" for c in criterios)


@lru_cache
def _build_instructions(equipo_primordial: str) -> str:
    template = _PROMPT_PATH.read_text(encoding="utf-8")
    catalog_text = _build_catalog_json()
    criterios = _build_criterios()
    prompt = template.replace("[CATALOGO_JSON]", catalog_text)
    prompt = prompt.replace("[CRITERIOS_DESAMBIGUACION]", criterios)
    return prompt.replace("[EQUIPO_PRIMORDIAL]", equipo_primordial)


def _parse_structured(data: dict) -> Capa2Result:
    tarea = data.get("tarea")
    equipo = data.get("equipo")
    tabla = data.get("tabla")

    if not equipo and not tabla:
        return Capa2Result(tarea=None, equipo=None, tabla=None, is_null=True)

    if not validate_classification(equipo, tabla):
        logger.warning(
            "Capa 2 devolvió combinación inválida equipo=%s tabla=%s — descartando",
            equipo, tabla,
        )
        return Capa2Result(tarea=None, equipo=None, tabla=None, is_null=True)

    return Capa2Result(tarea=tarea, equipo=equipo, tabla=tabla, is_null=False)


def _parse_response(raw: str) -> Capa2Result:
    """Parse legacy text format (kept for backward compatibility in tests)."""
    import re

    text = raw.strip()

    if text.upper() == "NULL" or not text:
        return Capa2Result(tarea=None, equipo=None, tabla=None, is_null=True)

    tarea = None
    equipo = None
    tabla = None

    match_tarea = re.search(r"TAREA QUE DEBE SER REGISTRADA:\s*(.+)", text)
    if match_tarea:
        tarea = match_tarea.group(1).strip()

    match_equipo = re.search(r"EQUIPO:\s*(.+)", text)
    if match_equipo:
        equipo = match_equipo.group(1).strip()

    match_tabla = re.search(r"TABLA:\s*(.+)", text)
    if match_tabla:
        tabla = match_tabla.group(1).strip()

    if not equipo and not tabla:
        return Capa2Result(tarea=None, equipo=None, tabla=None, is_null=True)

    return Capa2Result(tarea=tarea, equipo=equipo, tabla=tabla, is_null=False)


async def classify_capa2(
    message_text: str,
    equipo_primordial: str = "No especificado",
) -> Capa2Result:
    settings = get_settings()
    client = _get_client()
    instructions = _build_instructions(equipo_primordial)
    schema = _build_schema()

    try:
        response = await client.responses.create(
            model=settings.openai_model_capa2,
            instructions=instructions,
            input=message_text,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "capa2_response",
                    "strict": True,
                    "schema": schema,
                }
            },
            temperature=0.0,
            max_output_tokens=200,
        )
    except Exception:
        logger.exception("Capa 2: error en llamada a OpenAI")
        return Capa2Result(tarea=None, equipo=None, tabla=None, is_null=True)

    raw = response.output_text or ""
    logger.debug("Capa 2 raw response: %s", raw)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Capa 2: respuesta no parseable: %s", raw)
        return Capa2Result(tarea=None, equipo=None, tabla=None, is_null=True)

    return _parse_structured(data)
