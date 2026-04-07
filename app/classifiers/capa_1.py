from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.catalog.loader import load_catalog
from app.config.settings import get_settings
from app.services.openai_client import get_openai_client

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "capa_1.txt"


@dataclass
class Capa1Result:
    positivo: bool
    equipo_probable: str | None
    tabla_probable: str | None
    confianza: float
    motivo: str | None


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
            "positivo": {"type": "boolean"},
            "equipo_probable": {
                "anyOf": [
                    {"type": "string", "enum": valid_equipos},
                    {"type": "null"},
                ],
            },
            "tabla_probable": {
                "anyOf": [
                    {"type": "string", "enum": valid_tablas},
                    {"type": "null"},
                ],
            },
            "confianza": {"type": "number"},
            "motivo": {"type": "string"},
        },
        "required": ["positivo", "equipo_probable", "tabla_probable", "confianza", "motivo"],
        "additionalProperties": False,
    }


def _build_catalog_summary() -> str:
    catalog = load_catalog()
    summary: list[str] = []
    for equipo in catalog["equipos"]:
        tablas = [t["nombre"] for t in equipo["tablas"]]
        summary.append(f'Equipo: {equipo["nombre"]}\nTablas: {", ".join(tablas)}')
    return "\n\n".join(summary)


@lru_cache(maxsize=32)
def _build_instructions(equipo_primordial: str) -> str:
    template = _PROMPT_PATH.read_text(encoding="utf-8")
    catalog_text = _build_catalog_summary()
    prompt = template.replace("[CATALOGO_JSON]", catalog_text)
    return prompt.replace("[EQUIPO_PRIMORDIAL]", equipo_primordial)


def _make_error_result(motivo: str) -> Capa1Result:
    return Capa1Result(
        positivo=False,
        equipo_probable=None,
        tabla_probable=None,
        confianza=0.0,
        motivo=motivo,
    )


async def classify_capa1(
    message_text: str,
    equipo_primordial: str = "No especificado",
) -> Capa1Result:
    settings = get_settings()
    client = get_openai_client()
    instructions = _build_instructions(equipo_primordial)
    schema = _build_schema()

    try:
        response = await client.responses.create(
            model=settings.openai_model_capa1,
            instructions=instructions,
            input=message_text,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "capa1_response",
                    "strict": True,
                    "schema": schema,
                }
            },
            temperature=0.0,
            max_output_tokens=200,
        )
    except Exception:
        logger.exception("Capa 1: error en llamada a OpenAI")
        return _make_error_result("Error de conexión con IA")

    raw = response.output_text or ""
    logger.debug("Capa 1 raw response: %s", raw)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Capa 1: respuesta no parseable: %s", raw)
        return _make_error_result("Error al parsear respuesta de IA")

    return Capa1Result(
        positivo=bool(data.get("positivo", False)),
        equipo_probable=data.get("equipo_probable"),
        tabla_probable=data.get("tabla_probable"),
        confianza=float(data.get("confianza", 0.0)),
        motivo=data.get("motivo"),
    )
