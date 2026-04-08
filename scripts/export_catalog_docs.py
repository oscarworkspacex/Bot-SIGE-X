#!/usr/bin/env python3
"""Regenera Catalogo.txt en la raíz del repo desde app/catalog/catalog.json."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.catalog.loader import load_catalog  # noqa: E402


def main() -> None:
    load_catalog.cache_clear()
    catalog = load_catalog()

    lines: list[str] = [
        "Catálogo operativo (generado — no editar a mano).",
        "Fuente: app/catalog/catalog.json",
        "Regenerar: python scripts/export_catalog_docs.py",
        "",
        "Criterios de desambiguación (resumen):",
    ]
    for c in catalog.get("criterios_desambiguacion", []):
        lines.append(f"- {c}")
    lines.extend(["", "---", ""])

    for eq in catalog["equipos"]:
        lines.append(f"[{eq['nombre']}]")
        for t in eq["tablas"]:
            num = t.get("numero", "")
            name = t["nombre"]
            desc = (t.get("descripcion") or "").strip()
            lines.append(f"- {num}. {name}")
            if desc:
                lines.append(f"  Descripción: {desc}")
            ej = t.get("ejemplos") or []
            if ej:
                lines.append(f"  Ejemplos: {', '.join(ej)}")
            ex = t.get("exclusiones") or []
            for excl in ex:
                lines.append(f"  Exclusión: {excl}")
        lines.append("")

    out = ROOT / "Catalogo.txt"
    out.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    print(f"Escrito: {out}")


if __name__ == "__main__":
    main()
