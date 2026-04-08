"""Regresión: pipeline Capa 1 → Capa 2 con mocks (sin OpenAI ni dependencia de redacción del modelo).

Incluye heurísticas de síntesis canónica para Litigio → Escritos que deben ser presentados.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.classifiers.capa_1 import Capa1Result
from app.classifiers.capa_2 import Capa2Result
from app.classifiers.synthesis_quality import (
    colloquial_judge_markers_in_task,
    task_synthesis_ok_for_escritos_presentados,
)
from app.services.classifier_service import Decision, process_message


def _save_returns_id() -> SimpleNamespace:
    return SimpleNamespace(id=1)


@pytest.mark.asyncio
@patch("app.services.classifier_service.save_classification", new_callable=AsyncMock)
@patch("app.services.classifier_service.classify_capa2", new_callable=AsyncMock)
@patch("app.services.classifier_service.classify_capa1", new_callable=AsyncMock)
async def test_regression_copias_presentar_escrito_litigio_escritos(
    mock_c1: AsyncMock, mock_c2: AsyncMock, mock_save: AsyncMock,
) -> None:
    mock_save.return_value = _save_returns_id()
    mock_c1.return_value = Capa1Result(
        True, "Litigio", "Escritos que deben ser presentados", 0.85, "solicitud copias",
    )
    mock_c2.return_value = Capa2Result(
        "Presentar solicitud de copias certificadas",
        "Litigio",
        "Escritos que deben ser presentados",
        False,
    )
    r = await process_message(
        chat_id=1,
        message_id=1,
        text="Hay que presentar solicitud de copias certificadas de todo lo actuado",
    )
    assert r.decision == Decision.TASK_FOUND
    assert r.capa2 is not None
    assert r.capa2.equipo == "Litigio"
    assert r.capa2.tabla == "Escritos que deben ser presentados"
    assert task_synthesis_ok_for_escritos_presentados(r.capa2.tarea)


@pytest.mark.asyncio
@patch("app.services.classifier_service.save_classification", new_callable=AsyncMock)
@patch("app.services.classifier_service.classify_capa2", new_callable=AsyncMock)
@patch("app.services.classifier_service.classify_capa1", new_callable=AsyncMock)
async def test_regression_copias_pendientes_recoger(
    mock_c1: AsyncMock, mock_c2: AsyncMock, mock_save: AsyncMock,
) -> None:
    mock_save.return_value = _save_returns_id()
    mock_c1.return_value = Capa1Result(True, "Litigio", "Copias pendientes", 0.8, "copias listas")
    mock_c2.return_value = Capa2Result(
        "Recoger copias certificadas en juzgado",
        "Litigio",
        "Copias pendientes",
        False,
    )
    r = await process_message(
        chat_id=1,
        message_id=2,
        text="Las copias certificadas ya están listas para recoger en el juzgado",
    )
    assert r.decision == Decision.TASK_FOUND
    assert r.capa2 is not None
    assert r.capa2.tabla == "Copias pendientes"


@pytest.mark.asyncio
@patch("app.services.classifier_service.save_classification", new_callable=AsyncMock)
@patch("app.services.classifier_service.classify_capa2", new_callable=AsyncMock)
@patch("app.services.classifier_service.classify_capa1", new_callable=AsyncMock)
async def test_regression_declaraciones_sat_compliance(
    mock_c1: AsyncMock, mock_c2: AsyncMock, mock_save: AsyncMock,
) -> None:
    mock_save.return_value = _save_returns_id()
    mock_c1.return_value = Capa1Result(
        True, "Compliance Fiscal", "Declaraciones SAT que deben ser presentadas", 0.9, "sat",
    )
    mock_c2.return_value = Capa2Result(
        "Presentar declaraciones mensuales ante el SAT",
        "Compliance Fiscal",
        "Declaraciones SAT que deben ser presentadas",
        False,
    )
    r = await process_message(
        chat_id=1,
        message_id=3,
        text="Nos contrataron para presentar declaraciones mensuales ante el SAT sin operaciones",
    )
    assert r.decision == Decision.TASK_FOUND
    assert r.capa2 is not None
    assert r.capa2.equipo == "Compliance Fiscal"


@pytest.mark.asyncio
@patch("app.services.classifier_service.save_classification", new_callable=AsyncMock)
@patch("app.services.classifier_service.classify_capa2", new_callable=AsyncMock)
@patch("app.services.classifier_service.classify_capa1", new_callable=AsyncMock)
async def test_regression_condusef_der_financiero(
    mock_c1: AsyncMock, mock_c2: AsyncMock, mock_save: AsyncMock,
) -> None:
    mock_save.return_value = _save_returns_id()
    mock_c1.return_value = Capa1Result(
        True, "Der Financiero", "Quejas CONDUSEF que deben ser contestadas", 0.88, "condusef",
    )
    mock_c2.return_value = Capa2Result(
        "Contestar queja CONDUSEF",
        "Der Financiero",
        "Quejas CONDUSEF que deben ser contestadas",
        False,
    )
    r = await process_message(
        chat_id=1,
        message_id=4,
        text="Urge contestar la queja que entró en CONDUSEF por el cargo no reconocido",
    )
    assert r.decision == Decision.TASK_FOUND
    assert r.capa2 is not None
    assert r.capa2.equipo == "Der Financiero"


@pytest.mark.asyncio
@patch("app.services.classifier_service.save_classification", new_callable=AsyncMock)
@patch("app.services.classifier_service.classify_capa2", new_callable=AsyncMock)
@patch("app.services.classifier_service.classify_capa1", new_callable=AsyncMock)
async def test_regression_corporativo_impi(
    mock_c1: AsyncMock, mock_c2: AsyncMock, mock_save: AsyncMock,
) -> None:
    mock_save.return_value = _save_returns_id()
    mock_c1.return_value = Capa1Result(
        True, "Corporativo y laboral", "Ingresar trámite IMPI", 0.82, "impi",
    )
    mock_c2.return_value = Capa2Result(
        "Ingresar trámite ante IMPI",
        "Corporativo y laboral",
        "Ingresar trámite IMPI",
        False,
    )
    r = await process_message(
        chat_id=1,
        message_id=5,
        text="Registrar la marca ante el IMPI con la documentación que envió el cliente",
    )
    assert r.decision == Decision.TASK_FOUND
    assert r.capa2 is not None
    assert r.capa2.equipo == "Corporativo y laboral"


@pytest.mark.asyncio
@patch("app.services.classifier_service.save_classification", new_callable=AsyncMock)
@patch("app.services.classifier_service.classify_capa2", new_callable=AsyncMock)
@patch("app.services.classifier_service.classify_capa1", new_callable=AsyncMock)
async def test_regression_convenios_mediacion(
    mock_c1: AsyncMock, mock_c2: AsyncMock, mock_save: AsyncMock,
) -> None:
    mock_save.return_value = _save_returns_id()
    mock_c1.return_value = Capa1Result(True, "Convenios", "Convenios de mediación", 0.8, "mediacion")
    mock_c2.return_value = Capa2Result(
        "Elaborar convenio de mediación",
        "Convenios",
        "Convenios de mediación",
        False,
    )
    r = await process_message(
        chat_id=1,
        message_id=6,
        text="Hay que preparar el convenio de mediación entre las partes para la próxima sesión",
    )
    assert r.decision == Decision.TASK_FOUND
    assert r.capa2 is not None
    assert r.capa2.equipo == "Convenios"


@pytest.mark.asyncio
@patch("app.services.classifier_service.save_classification", new_callable=AsyncMock)
@patch("app.services.classifier_service.classify_capa2", new_callable=AsyncMock)
@patch("app.services.classifier_service.classify_capa1", new_callable=AsyncMock)
async def test_regression_hablar_juez_presencial(
    mock_c1: AsyncMock, mock_c2: AsyncMock, mock_save: AsyncMock,
) -> None:
    mock_save.return_value = _save_returns_id()
    mock_c1.return_value = Capa1Result(
        True, "Litigio", "Hablar con jueces y magistrados", 0.75, "cita juez",
    )
    mock_c2.return_value = Capa2Result(
        "Acudir personalmente a cita con el juez",
        "Litigio",
        "Hablar con jueces y magistrados",
        False,
    )
    r = await process_message(
        chat_id=1,
        message_id=7,
        text="Hay que ir personalmente a ver al juez mañana a las 10 para explicar el tema",
    )
    assert r.decision == Decision.TASK_FOUND
    assert r.capa2 is not None
    assert r.capa2.tabla == "Hablar con jueces y magistrados"


@pytest.mark.asyncio
@patch("app.services.classifier_service.save_classification", new_callable=AsyncMock)
@patch("app.services.classifier_service.classify_capa2", new_callable=AsyncMock)
@patch("app.services.classifier_service.classify_capa1", new_callable=AsyncMock)
async def test_regression_capa1_negative_stops_before_capa2(
    mock_c1: AsyncMock, mock_c2: AsyncMock, mock_save: AsyncMock,
) -> None:
    mock_save.return_value = _save_returns_id()
    mock_c1.return_value = Capa1Result(False, None, None, 0.2, "sin tarea")
    r = await process_message(
        chat_id=1,
        message_id=8,
        text="Este mensaje parece una tarea pero capa1 lo niega en este escenario de prueba",
    )
    assert r.decision == Decision.CAPA1_NEGATIVE
    assert r.capa2 is None
    mock_c2.assert_not_called()


@pytest.mark.asyncio
@patch("app.services.classifier_service.save_classification", new_callable=AsyncMock)
@patch("app.services.classifier_service.classify_capa2", new_callable=AsyncMock)
@patch("app.services.classifier_service.classify_capa1", new_callable=AsyncMock)
async def test_regression_capa2_null(
    mock_c1: AsyncMock, mock_c2: AsyncMock, mock_save: AsyncMock,
) -> None:
    mock_save.return_value = _save_returns_id()
    mock_c1.return_value = Capa1Result(True, "Litigio", "Escritos de fondo", 0.5, "duda")
    mock_c2.return_value = Capa2Result(None, None, None, True)
    r = await process_message(
        chat_id=1,
        message_id=9,
        text="Mensaje ambiguo que en este mock no produce tabla válida en capa dos",
    )
    assert r.decision == Decision.CAPA2_NULL
    assert r.capa2 is not None
    assert r.capa2.is_null


@pytest.mark.asyncio
@patch("app.services.classifier_service.save_classification", new_callable=AsyncMock)
@patch("app.services.classifier_service.classify_capa2", new_callable=AsyncMock)
@patch("app.services.classifier_service.classify_capa1", new_callable=AsyncMock)
async def test_regression_invalid_equipo_tabla_combo_rejected(
    mock_c1: AsyncMock, mock_c2: AsyncMock, mock_save: AsyncMock,
) -> None:
    mock_save.return_value = _save_returns_id()
    mock_c1.return_value = Capa1Result(True, "Litigio", "Escritos de fondo", 0.7, "test")
    mock_c2.return_value = Capa2Result(
        "Algo",
        "Litigio",
        "Quejas CONDUSEF que deben ser contestadas",
        False,
    )
    r = await process_message(
        chat_id=1,
        message_id=10,
        text="Escenario donde el modelo devuelve tabla que no corresponde al equipo",
    )
    assert r.decision == Decision.TASK_INVALID_CATALOG
    assert r.catalog_valid is False
    assert r.capa2 is not None
    assert r.capa2.is_null is False


@pytest.mark.parametrize(
    "tarea",
    [
        "Presentar escrito para habilitar días y horas inhábiles",
        "Presentar solicitud de copias certificadas",
        "Promover incidente de liquidación de sentencia",
    ],
)
def test_synthesis_canonical_escritos_has_no_colloquial_markers(tarea: str) -> None:
    assert task_synthesis_ok_for_escritos_presentados(tarea)
    assert colloquial_judge_markers_in_task(tarea) == ()


@pytest.mark.parametrize(
    "tarea",
    [
        "Dile al juez que habilite días inhábiles",
        "Pídele al magistrado que acuerde la solicitud",
        "Háblale al MP para que libre el oficio",
    ],
)
def test_synthesis_colloquial_detected_for_regression(tarea: str) -> None:
    assert not task_synthesis_ok_for_escritos_presentados(tarea)
    assert len(colloquial_judge_markers_in_task(tarea)) >= 1


def test_synthesis_empty_task_no_false_positives() -> None:
    assert task_synthesis_ok_for_escritos_presentados(None)
    assert task_synthesis_ok_for_escritos_presentados("")
    assert colloquial_judge_markers_in_task(None) == ()
