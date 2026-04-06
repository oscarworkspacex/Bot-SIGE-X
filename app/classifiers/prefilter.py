"""
Pre-filtro local ultra-barato para descartar mensajes obviamente irrelevantes
antes de hacer cualquier llamada a OpenAI.

Criterio: solo rechaza lo que es CLARAMENTE irrelevante.
En caso de duda, deja pasar (return True).
"""
from __future__ import annotations

import re
import unicodedata

_EMOJI_PATTERN = re.compile(
    "[\U0001f600-\U0001f64f"
    "\U0001f300-\U0001f5ff"
    "\U0001f680-\U0001f6ff"
    "\U0001f1e0-\U0001f1ff"
    "\U00002702-\U000027b0"
    "\U000024c2-\U0001f251"
    "\U0001f900-\U0001f9ff"
    "\U0001fa00-\U0001fa6f"
    "\U0001fa70-\U0001faff"
    "\U00002600-\U000026ff"
    "]+",
    flags=re.UNICODE,
)

_GREETINGS = frozenset({
    "hola", "hi", "hello", "hey", "buenos dias", "buenas tardes",
    "buenas noches", "buen dia", "que tal", "como estas", "como estan",
    "saludos", "q tal", "k tal", "ke tal", "buenas",
})

_CASUAL_FILLERS = frozenset({
    "ok", "okey", "okay", "vale", "va", "sale", "dale", "si", "sí",
    "no", "nop", "nel", "aja", "ajá", "mmm", "hmm", "ah", "oh",
    "jaja", "jajaja", "jajajaja", "xd", "lol", "ja", "je", "jeje",
    "gracias", "grax", "thx", "thanks", "de nada", "porfa", "porfavor",
    "por favor", "claro", "exacto", "perfecto", "listo", "genial",
    "bien", "muy bien", "excelente", "cool", "nice",
    "👍", "👌", "🙏", "😊", "😂", "🤣", "❤️", "💯",
    "ya", "orale", "andale", "simon", "nel pastel", "va va",
    "todo bien", "que onda", "nos vemos", "hasta luego",
    "bye", "adios", "chao", "a la orden", "con gusto",
})

MIN_CHARS_FOR_TASK = 4


def normalize_text(raw: str) -> str:
    text = raw.strip()
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _strip_accents(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _strip_emojis(text: str) -> str:
    return _EMOJI_PATTERN.sub("", text).strip()


def passes_prefilter(text: str) -> bool:
    """
    Devuelve True si el mensaje DEBE seguir al pipeline de clasificación.
    Devuelve False si es claramente irrelevante (saludo, emoji, casual).
    """
    normalized = normalize_text(text)

    if len(normalized) < MIN_CHARS_FOR_TASK:
        return False

    without_emojis = _strip_emojis(normalized)
    if not without_emojis:
        return False

    lower = without_emojis.lower().strip()
    lower_no_accents = _strip_accents(lower)
    lower_clean = re.sub(r"[¿¡!?,.\-;:\"'()]+", "", lower_no_accents).strip()

    if lower_clean in _GREETINGS:
        return False

    if lower_clean in _CASUAL_FILLERS:
        return False

    words = lower_clean.split()
    if len(words) <= 2 and all(w in _GREETINGS | _CASUAL_FILLERS for w in words):
        return False

    return True
