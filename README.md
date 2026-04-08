# Bot Sige X — Rusconi Consulting

Bot de Telegram para notificaciones y registro de tareas de un despacho jurídico-operativo. Clasifica mensajes entrantes en dos capas (filtrado amplio + clasificación exacta) contra un catálogo cerrado de tareas y equipos.

## Requisitos

- Python 3.12+
- Token de bot de Telegram (obtener vía [@BotFather](https://t.me/BotFather))
- API key de OpenAI

## Instalación

```bash
# Clonar o ubicarse en el directorio del proyecto
cd "Proyecto Bot Sige X"

# Crear entorno virtual
python -m venv .venv

# Activar entorno virtual
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Linux/macOS:
# source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

## Variables de entorno

Copiar `.env.example` a `.env` y completar los valores:

```bash
cp .env.example .env
```

| Variable | Descripción |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Token del bot obtenido de BotFather |
| `OPENAI_API_KEY` | API key de OpenAI |
| `OPENAI_MODEL_CAPA1` | Modelo para filtrado amplio (default: `gpt-4o-mini`) |
| `OPENAI_MODEL_CAPA2` | Modelo para clasificación exacta (default: `gpt-4o`) |
| `DATABASE_URL` | URL de la base de datos (default: `sqlite+aiosqlite:///data/bot.db`) |
| `LOG_LEVEL` | Nivel de logging: DEBUG, INFO, WARNING, ERROR (default: `INFO`) |

## Cómo correr el bot

```bash
python main.py
```

Esto arranca simultáneamente:
- El bot de Telegram en modo **polling** (desarrollo local)
- Un servidor FastAPI en `http://localhost:8000` con endpoint `/health`

## Cómo probarlo en Telegram

1. Buscar el bot por su username en Telegram
2. Enviar `/start` — el bot responde con un mensaje de bienvenida
3. Enviar cualquier mensaje de texto — el bot lo clasifica usando las dos capas y responde con el resultado

## Estructura del proyecto

```
app/
  config/       Configuración y variables de entorno
  bot/          Handlers de Telegram (/start, mensajes)
  classifiers/  Capa 1 (filtro amplio) y Capa 2 (clasificación exacta)
  prompts/      Templates de prompts para OpenAI
  catalog/      Catálogo cerrado de tareas y equipos (JSON)
  models/       Modelos de base de datos (SQLAlchemy)
  storage/      Motor de DB y repositorio de acceso a datos
  services/     Lógica de negocio y orquestación
  api/          Endpoints FastAPI (health, webhook futuro)
tests/          Tests de humo
data/           Base de datos SQLite (no versionada)
```

### Catálogo (fuente única)

- La **única fuente canónica** de equipos, tablas, descripciones y exclusiones es `app/catalog/catalog.json`.
- **Capa 1** y **Capa 2** arman sus prompts a partir de ese JSON (Capa 2 ya no duplica el catálogo en el archivo de prompt).
- `Catalogo.txt` en la raíz es un **resumen generado**; para actualizarlo tras cambiar el JSON:

```bash
python scripts/export_catalog_docs.py
```

Los archivos `Capa 1.txt` y `Capa 2 nueva.txt` en la raíz son **punteros** al contenido real bajo `app/prompts/` y `app/catalog/`.

## Tests

```bash
pytest tests/ -v
```

Incluye pruebas de humo (`test_smoke.py`) y regresión del pipeline con mocks (`test_regression_classification.py`), más heurísticas de síntesis canónica en `app/classifiers/synthesis_quality.py` (uso en CI/tests, no altera respuestas en runtime).
