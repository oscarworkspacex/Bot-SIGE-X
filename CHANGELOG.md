# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/).

## [1.0.0] — 2026-04-08

### Añadido

- `app/catalog/bundle_manifest.json`: versión lógica del paquete catálogo + prompts (`bundle_version`).
- `eval/golden_cases.json` y `scripts/evaluate_golden_set.py`: evaluación **opcional** contra el modelo real (`--live`).
- `docs/operacion_y_versionado.md`: guía de versionado, evaluación y monitoreo.

### Notas

- Cualquier cambio futuro a `catalog.json`, `capa_1.txt` o `capa_2.txt` debe ir acompañado de incremento de `bundle_version` y entrada aquí.
