"""Smoke tests: verifican imports, config, catálogo, modelos, health, parseo y prefilter."""

from __future__ import annotations

import os

import pytest
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///data/test.db")


# --- Config ---

def test_settings_load():
    from app.config.settings import get_settings
    get_settings.cache_clear()
    s = get_settings()
    assert s.telegram_bot_token
    assert s.openai_api_key
    assert "sqlite" in s.database_url


def test_setup_logging():
    from app.config.settings import setup_logging
    setup_logging("DEBUG")


# --- Catálogo ---

def test_catalog_loads():
    from app.catalog.loader import load_catalog
    catalog = load_catalog()
    assert "equipos" in catalog
    assert "criterios_desambiguacion" in catalog


def test_catalog_has_5_equipos():
    from app.catalog.loader import get_equipos
    equipos = get_equipos()
    assert len(equipos) == 5
    expected = {"Litigio", "Corporativo y laboral", "Convenios", "Der Financiero", "Compliance Fiscal"}
    assert set(equipos) == expected


def test_catalog_tablas_by_equipo():
    from app.catalog.loader import get_tablas_by_equipo
    tablas_lit = get_tablas_by_equipo("Litigio")
    assert len(tablas_lit) == 21
    tablas_fin = get_tablas_by_equipo("Der Financiero")
    assert len(tablas_fin) == 16
    tablas_comp = get_tablas_by_equipo("Compliance Fiscal")
    assert len(tablas_comp) == 15
    tablas_corp = get_tablas_by_equipo("Corporativo y laboral")
    assert len(tablas_corp) == 14
    tablas_conv = get_tablas_by_equipo("Convenios")
    assert len(tablas_conv) == 4


def test_catalog_find_tabla():
    from app.catalog.loader import find_tabla
    t = find_tabla("Litigio", "Escritos de fondo")
    assert t is not None
    assert t["numero"] == 1


def test_catalog_validate_classification():
    from app.catalog.loader import validate_classification
    assert validate_classification("Litigio", "Escritos de fondo") is True
    assert validate_classification("Litigio", "Tabla inventada") is False
    assert validate_classification(None, None) is False
    assert validate_classification("Equipo inventado", "Tabla") is False


def test_catalog_unknown_equipo_returns_empty():
    from app.catalog.loader import get_tablas_by_equipo
    assert get_tablas_by_equipo("No existe") == []


# --- Prompts ---

def test_prompts_capa1_exists_and_has_placeholder():
    from pathlib import Path
    prompt_path = Path(__file__).parent.parent / "app" / "prompts" / "capa_1.txt"
    text = prompt_path.read_text(encoding="utf-8")
    assert "[EQUIPO_PRIMORDIAL]" in text
    assert "[CATALOGO_JSON]" in text
    assert "positivo" in text
    assert "confianza" in text


def test_prompts_capa2_exists_and_has_placeholder():
    from pathlib import Path
    prompt_path = Path(__file__).parent.parent / "app" / "prompts" / "capa_2.txt"
    text = prompt_path.read_text(encoding="utf-8")
    assert "[EQUIPO_PRIMORDIAL]" in text
    assert "[CATALOGO_JSON]" not in text
    assert "[CRITERIOS_DESAMBIGUACION]" not in text
    assert "CATÁLOGO CERRADO DE TAREAS PERMITIDAS" in text
    assert "CRITERIOS DE DESAMBIGUACIÓN" in text
    assert "tarea" in text.lower()
    assert "equipo" in text.lower()
    assert "tabla" in text.lower()


# --- Pre-filtro ---

def test_prefilter_rejects_greetings():
    from app.classifiers.prefilter import passes_prefilter
    assert passes_prefilter("hola") is False
    assert passes_prefilter("Buenos días") is False
    assert passes_prefilter("Buenas tardes!") is False
    assert passes_prefilter("Saludos") is False


def test_prefilter_rejects_casual():
    from app.classifiers.prefilter import passes_prefilter
    assert passes_prefilter("ok") is False
    assert passes_prefilter("jajaja") is False
    assert passes_prefilter("gracias") is False
    assert passes_prefilter("👍") is False
    assert passes_prefilter("sí") is False
    assert passes_prefilter("Jaja gracias") is False
    assert passes_prefilter("hola gracias") is False
    assert passes_prefilter("Ok perfecto") is False
    assert passes_prefilter("ya listo") is False


def test_prefilter_rejects_emojis_only():
    from app.classifiers.prefilter import passes_prefilter
    assert passes_prefilter("😊🎉👏") is False
    assert passes_prefilter("❤️") is False


def test_prefilter_rejects_short():
    from app.classifiers.prefilter import passes_prefilter
    assert passes_prefilter("ab") is False
    assert passes_prefilter("") is False


def test_prefilter_passes_task_like():
    from app.classifiers.prefilter import passes_prefilter
    assert passes_prefilter("Necesito abrir una cuenta bancaria para el cliente") is True
    assert passes_prefilter("Hay que contestar la queja de CONDUSEF") is True
    assert passes_prefilter("El requerimiento de la CNBV vence mañana") is True
    assert passes_prefilter("Declaración anual de la empresa") is True


def test_prefilter_passes_ambiguous():
    from app.classifiers.prefilter import passes_prefilter
    assert passes_prefilter("manda el documento al SAT por favor") is True
    assert passes_prefilter("hay que checar lo del IMSS") is True


def test_normalize_text():
    from app.classifiers.prefilter import normalize_text
    assert normalize_text("  hola   mundo  ") == "hola mundo"
    assert normalize_text("\n\ttexto\n") == "texto"


# --- Clasificadores (unit) ---

def test_confidence_normalize():
    from app.classifiers.confidence import normalize_confidence
    assert normalize_confidence(1.5) == 1.0
    assert normalize_confidence(-0.3) == 0.0
    assert normalize_confidence(0.7) == pytest.approx(0.7)


def test_confidence_combined():
    from app.classifiers.confidence import compute_combined_confidence
    assert compute_combined_confidence(0.8, capa2_is_null=True) == pytest.approx(0.24)
    assert compute_combined_confidence(0.8, capa2_is_null=False) == pytest.approx(0.96)
    assert compute_combined_confidence(1.0, capa2_is_null=False) == 1.0


def test_capa2_parse_structured_all_none():
    from app.classifiers.capa_2 import _parse_structured
    r = _parse_structured({"tarea": None, "equipo": None, "tabla": None})
    assert r.is_null is True


def test_capa2_parse_structured_missing_keys():
    from app.classifiers.capa_2 import _parse_structured
    r = _parse_structured({})
    assert r.is_null is True


def test_capa2_parse_structured_valid():
    from app.classifiers.capa_2 import _parse_structured
    data = {
        "tarea": "Abrir cuenta bancaria",
        "equipo": "Der Financiero",
        "tabla": "Cuentas bancarias y similares en proceso",
    }
    r = _parse_structured(data)
    assert r.is_null is False
    assert r.equipo == "Der Financiero"
    assert r.tabla == "Cuentas bancarias y similares en proceso"


def test_capa2_parse_structured_null():
    from app.classifiers.capa_2 import _parse_structured
    data_null = {"tarea": None, "equipo": None, "tabla": None}
    r = _parse_structured(data_null)
    assert r.is_null is True


def test_capa2_parse_structured_rejects_invalid_equipo():
    from app.classifiers.capa_2 import _parse_structured
    data = {
        "tarea": "Responder oficio CNBV",
        "equipo": "Regulatorio",
        "tabla": "Desahogos de requerimientos",
    }
    r = _parse_structured(data)
    assert r.is_null is True


def test_capa2_parse_structured_rejects_invalid_tabla():
    from app.classifiers.capa_2 import _parse_structured
    data = {
        "tarea": "Algo",
        "equipo": "Der Financiero",
        "tabla": "Tabla inventada que no existe",
    }
    r = _parse_structured(data)
    assert r.is_null is True


def test_capa2_schema_has_enum_constraints():
    from app.classifiers.capa_2 import _build_schema
    schema = _build_schema()
    equipo_prop = schema["properties"]["equipo"]
    equipo_enum = equipo_prop["anyOf"][0]["enum"]
    assert "Litigio" in equipo_enum
    assert "Der Financiero" in equipo_enum
    assert "Regulatorio" not in equipo_enum
    assert len(equipo_enum) == 5

    tabla_prop = schema["properties"]["tabla"]
    tabla_enum = tabla_prop["anyOf"][0]["enum"]
    assert "Copias pendientes" in tabla_enum
    assert "Escritos de fondo" in tabla_enum
    assert len(tabla_enum) > 50


# --- Modelos ---

def test_classification_model():
    from app.models.database import Classification
    columns = {c.name for c in Classification.__table__.columns}
    expected = {
        "id", "telegram_chat_id", "telegram_message_id", "raw_text",
        "capa1_positivo", "capa1_equipo", "capa1_tabla", "capa1_confianza", "capa1_motivo",
        "capa2_equipo", "capa2_tabla", "capa2_tarea",
        "decision_final", "created_at",
    }
    assert expected == columns


# --- Decision constants ---

def test_decision_constants():
    from app.services.classifier_service import Decision
    assert Decision.PREFILTER_REJECTED == "prefilter_rejected"
    assert Decision.CAPA1_NEGATIVE == "capa1_negative"
    assert Decision.CAPA2_NULL == "capa2_null"
    assert Decision.TASK_FOUND == "task_found"


# --- Health endpoint ---

@pytest.mark.asyncio
async def test_health_endpoint():
    from app.config.settings import get_settings
    get_settings.cache_clear()

    from main import app

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "bot-sige-x"
