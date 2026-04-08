#!/usr/bin/env python3
"""
Evaluación opcional contra el modelo real (OpenAI). No forma parte del arranque del bot.

Uso:
  python scripts/evaluate_golden_set.py
      → muestra manifiesto y ayuda (sin llamadas a API).

  python scripts/evaluate_golden_set.py --live
      → ejecuta los casos en eval/golden_cases.json (requiere .env con API key).

  python scripts/evaluate_golden_set.py --live --fail-on-mismatch
      → exit code 1 si algún caso no cumple expectativas.

No modifica catálogo ni prompts; solo lee y compara salidas.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _print_manifest() -> None:
    manifest_path = ROOT / "app" / "catalog" / "bundle_manifest.json"
    if manifest_path.is_file():
        data = _load_json(manifest_path)
        print(f"Manifiesto de versión: {manifest_path}")
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print("No se encontró bundle_manifest.json", file=sys.stderr)


async def _run_live(cases_path: Path, fail_on_mismatch: bool) -> int:
    from app.classifiers.capa_1 import classify_capa1
    from app.classifiers.capa_2 import classify_capa2
    from app.classifiers.prefilter import normalize_text, passes_prefilter

    data = _load_json(cases_path)
    case_list = data.get("cases") or []
    if not case_list:
        print("No hay casos en el archivo.", file=sys.stderr)
        return 1

    failures = 0
    print(f"Casos: {len(case_list)} (archivo: {cases_path})\n")

    for case in case_list:
        cid = case.get("id", "?")
        text = case.get("text") or ""
        expect = case.get("expect") or {}
        exp_eq = expect.get("equipo")
        exp_tab = expect.get("tabla")
        exp_c1_pos = case.get("expect_capa1_positivo")

        normalized = normalize_text(text)
        ok = True
        detail_parts: list[str] = []
        c1_pos: bool | None = None
        c1_eq_prob = c1_tab_prob = None
        c2_eq = c2_tab = None
        c2_null = True

        if not passes_prefilter(normalized):
            ok = False
            detail_parts.append("pre-filtro rechazó el texto")
        else:
            capa1 = await classify_capa1(normalized, "No especificado")
            c1_pos = capa1.positivo
            c1_eq_prob = capa1.equipo_probable
            c1_tab_prob = capa1.tabla_probable

            if exp_c1_pos is not None and c1_pos != exp_c1_pos:
                ok = False
                detail_parts.append(
                    f"Capa1 positivo={c1_pos}, se esperaba {exp_c1_pos}",
                )

            if not capa1.positivo:
                if exp_eq or exp_tab:
                    ok = False
                    detail_parts.append("Capa 1 negativa; no se ejecutó Capa 2")
            else:
                capa2 = await classify_capa2(normalized, "No especificado")
                c2_eq, c2_tab = capa2.equipo, capa2.tabla
                c2_null = capa2.is_null
                if capa2.is_null:
                    ok = False
                    detail_parts.append("Capa 2 devolvió null")
                elif exp_eq and exp_tab:
                    if capa2.equipo != exp_eq or capa2.tabla != exp_tab:
                        ok = False
                        detail_parts.append(
                            f"Capa2 {capa2.equipo} / {capa2.tabla} ≠ esperado {exp_eq} / {exp_tab}",
                        )

        if not detail_parts:
            detail_parts.append("coincide con expect")

        status = "OK" if ok else "FAIL"
        if not ok:
            failures += 1

        print(f"[{status}] {cid}")
        print(f"  texto: {text[:88]}{'…' if len(text) > 88 else ''}")
        if c1_pos is not None:
            print(f"  Capa1 positivo={c1_pos} probable={c1_eq_prob} / {c1_tab_prob}")
        if not c2_null or c2_eq is not None:
            print(f"  Capa2 equipo={c2_eq} tabla={c2_tab} null={c2_null}")
        print(f"  {'; '.join(detail_parts)}\n")

    print(f"Resumen: {failures} fallos de {len(case_list)}")
    if fail_on_mismatch and failures:
        return 1
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluación opcional golden set (LLM real).")
    parser.add_argument(
        "--cases",
        type=Path,
        default=ROOT / "eval" / "golden_cases.json",
        help="Ruta al JSON de casos",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Llamar a OpenAI (costo API). Sin este flag no se hacen llamadas.",
    )
    parser.add_argument(
        "--fail-on-mismatch",
        action="store_true",
        help="Exit code 1 si hay fallos (solo con --live).",
    )
    args = parser.parse_args()

    _print_manifest()
    print()

    if not args.live:
        print("Modo sin API: no se ejecutaron clasificaciones.")
        print("Para correr contra el modelo real:")
        print(f"  python scripts/evaluate_golden_set.py --live --cases {args.cases}")
        print("Documentación: docs/operacion_y_versionado.md")
        return

    if not args.cases.is_file():
        print(f"No existe {args.cases}", file=sys.stderr)
        sys.exit(1)

    code = asyncio.run(_run_live(args.cases, args.fail_on_mismatch))
    sys.exit(code)


if __name__ == "__main__":
    main()
