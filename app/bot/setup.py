from __future__ import annotations

import logging

from telegram.ext import Application, MessageHandler, CommandHandler, filters

from app.bot.handlers import handle_message, start_command
from app.config.settings import get_settings

logger = logging.getLogger(__name__)


def create_bot_application() -> Application:
    settings = get_settings()
    app = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .build()
    )

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(
        MessageHandler(filters.Document.ALL | filters.PHOTO, handle_message)
    )

    logger.info("Bot de Telegram configurado")
    return app
