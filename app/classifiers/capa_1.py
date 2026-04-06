from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

from openai import AsyncOpenAI

from app.config.settings import get_settings

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "capa_1.txt"
_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=get_settings().openai_api_key)
    return _client


@dataclass
class Capa1Result:
    positivo: bool
    equipo_probable: str | None
    tabla_probable: str | None
    confianza: float
    motivo: str | None


def _load_prompt(equipo_primordial: str = "No especificado") -> str:
    text = _PROMPT_PATH.read_text(encoding="utf-8")
    return text.replace("[EQUIPO_PRIMORDIAL]", equipo_primordial)


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
    client = _get_client()
    system_prompt = _load_prompt(equipo_primordial)

    try:
        response = await client.chat.completions.create(
            model=settings.openai_model_capa1,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message_text},
            ],
            temperature=0.0,
        )
    except Exception:
        logger.exception("Capa 1: error en llamada a OpenAI")
        return _make_error_result("Error de conexión con IA")

    raw = response.choices[0].message.content or ""
    logger.debug("Capa 1 raw response: %s", raw)

    try:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
        data = json.loads(cleaned)
    except (json.JSONDecodeError, IndexError):
        logger.warning("Capa 1: respuesta no parseable: %s", raw)
        return _make_error_result("Error al parsear respuesta de IA")

    return Capa1Result(
        positivo=bool(data.get("positivo", False)),
        equipo_probable=data.get("equipo_probable"),
        tabla_probable=data.get("tabla_probable"),
        confianza=float(data.get("confianza", 0.0)),
        motivo=data.get("motivo"),
    )
