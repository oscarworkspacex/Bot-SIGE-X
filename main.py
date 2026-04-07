from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.api.health import router as health_router
from app.bot.setup import create_bot_application
from app.config.settings import get_settings, setup_logging
from app.storage.engine import close_db, init_db

logger = logging.getLogger(__name__)


async def _run_bot_polling(app: FastAPI) -> None:
    bot_app = create_bot_application()
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling(drop_pending_updates=True)
    app.state.bot_app = bot_app
    logger.info("Bot de Telegram iniciado en modo polling")


async def _stop_bot_polling(app: FastAPI) -> None:
    bot_app = getattr(app.state, "bot_app", None)
    if bot_app is not None:
        await bot_app.updater.stop()
        await bot_app.stop()
        await bot_app.shutdown()
        logger.info("Bot de Telegram detenido")


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Iniciando Bot Sige X...")

    await init_db()
    await _run_bot_polling(app)

    yield

    await _stop_bot_polling(app)
    await close_db()
    logger.info("Bot Sige X apagado")


app = FastAPI(
    title="Bot Sige X",
    description="API de soporte para el bot de Telegram de Rusconi Consulting",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health_router)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level=get_settings().log_level.lower(),
    )
