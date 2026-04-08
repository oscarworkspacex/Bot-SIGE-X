# Operación, versionado y evaluación (sin tocar el núcleo)

Este documento describe **buenas prácticas** alrededor del bot. No altera el comportamiento en runtime; el código de clasificación sigue en `app/classifiers/`, `app/prompts/` y `app/catalog/catalog.json`.

## 1. Congelar el conjunto catálogo + prompts

Tratar como un **solo paquete versionado**:

| Artefacto | Ruta |
|-----------|------|
| Catálogo | `app/catalog/catalog.json` |
| Prompt Capa 1 | `app/prompts/capa_1.txt` |
| Prompt Capa 2 | `app/prompts/capa_2.txt` |

El archivo `app/catalog/bundle_manifest.json` lleva un **`bundle_version`** semántico (p. ej. `1.0.0`). **Sube la versión** cuando cambies cualquiera de los tres componentes y anota el motivo en `CHANGELOG.md`.

Así evitas *drift* silencioso y sabes qué desplegaste.

## 2. Evaluación opcional con modelo real (set dorado)

- Casos: `eval/golden_cases.json`
- Script: `scripts/evaluate_golden_set.py`

**Sin costo de API** (solo muestra manifiesto y ayuda):

```bash
python scripts/evaluate_golden_set.py
```

**Con llamadas reales** (requiere `.env` con `OPENAI_API_KEY` y el resto de variables del proyecto):

```bash
python scripts/evaluate_golden_set.py --live
```

Para fallar con código de salida distinto de cero si algo no coincide (jobs manuales o CI opcional):

```bash
python scripts/evaluate_golden_set.py --live --fail-on-mismatch
```

El LLM puede variar; los casos son **objetivo de calidad**, no una prueba determinista al 100 %.

## 3. Monitoreo operativo sugerido (1–2 semanas tras cambios)

- Mensajes que el equipo **corrige manualmente** tras la clasificación del bot.
- Tasa de decisiones `capa2_null` o `task_invalid_catalog` frente a `task_found`.
- Confusiones entre **tablas vecinas** (p. ej. Escritos que deben ser presentados vs Copias pendientes; Escritos vs Hablar con jueces).

Ajusta prompts o catálogo solo ante **bugs reales** o datos de monitoreo, y vuelve a subir `bundle_version` + entrada en `CHANGELOG.md`.

## 4. Regenerar vista en texto del catálogo

Tras editar `catalog.json`:

```bash
python scripts/export_catalog_docs.py
```
