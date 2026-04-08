"""Esquema de manifiesto y casos dorados (sin llamar a OpenAI)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_bundle_manifest_schema():
    path = ROOT / "app" / "catalog" / "bundle_manifest.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "bundle_version" in data
    assert "components" in data
    comps = data["components"]
    assert "catalog" in comps
    assert "prompt_capa1" in comps
    assert "prompt_capa2" in comps


def test_golden_cases_schema():
    path = ROOT / "eval" / "golden_cases.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    cases = data.get("cases") or []
    assert len(cases) >= 1
    for c in cases:
        assert "id" in c
        assert c.get("text")
        exp = c.get("expect") or {}
        assert exp.get("equipo")
        assert exp.get("tabla")
