from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from app.services.classifier_service import Decision, process_message

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    await update.message.reply_text(
        "Hola, soy el bot de registro de tareas de Rusconi Consulting.\n\n"
        "Monitoreo los mensajes del grupo y detecto automáticamente "
        "tareas registrables del catálogo del despacho.\n\n"
        "Comandos disponibles:\n"
        "/start — Mostrar este mensaje"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    text = update.message.text or update.message.caption or ""
    if not text.strip():
        return

    chat_id = update.message.chat_id
    message_id = update.message.message_id

    try:
        result = await process_message(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
        )

        if result.decision == Decision.TASK_FOUND and result.capa2:
            await update.message.reply_text(
                f"Tarea detectada\n"
                f"Equipo: {result.capa2.equipo}\n"
                f"Tabla: {result.capa2.tabla}"
            )

    except Exception:
        logger.exception("Error procesando mensaje chat=%s msg=%s", chat_id, message_id)
