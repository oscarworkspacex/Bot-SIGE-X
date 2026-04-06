from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path

from openai import AsyncOpenAI

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


def _load_prompt(equipo_primordial: str = "No especificado") -> str:
    text = _PROMPT_PATH.read_text(encoding="utf-8")
    return text.replace("[EQUIPO_PRIMORDIAL]", equipo_primordial)


def _parse_response(raw: str) -> Capa2Result:
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
    system_prompt = _load_prompt(equipo_primordial)

    try:
        response = await client.chat.completions.create(
            model=settings.openai_model_capa2,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message_text},
            ],
            temperature=0.0,
        )
    except Exception:
        logger.exception("Capa 2: error en llamada a OpenAI")
        return Capa2Result(tarea=None, equipo=None, tabla=None, is_null=True)

    raw = response.choices[0].message.content or ""
    logger.debug("Capa 2 raw response: %s", raw)

    return _parse_response(raw)
