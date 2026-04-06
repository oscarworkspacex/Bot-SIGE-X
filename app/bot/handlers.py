from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from app.services.classifier_service import process_message

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hola, soy el bot de registro de tareas de Rusconi Consulting.\n\n"
        "Envíame un mensaje y lo clasificaré automáticamente según el catálogo "
        "de tareas del despacho.\n\n"
        "Comandos disponibles:\n"
        "/start — Mostrar este mensaje"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    chat_id = update.message.chat_id
    message_id = update.message.message_id
    text = update.message.text

    await update.message.reply_text("Analizando tu mensaje...")

    try:
        result = await process_message(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
        )

        if not result.capa1.positivo:
            await update.message.reply_text(
                "No se detectó una tarea registrable en tu mensaje.\n"
                f"Motivo: {result.capa1.motivo or 'Sin coincidencia con el catálogo'}"
            )
            return

        if result.capa2 and not result.capa2.is_null:
            validity = "En catálogo" if result.catalog_valid else "Fuera de catálogo"
            await update.message.reply_text(
                f"Tarea detectada:\n\n"
                f"Equipo: {result.capa2.equipo}\n"
                f"Tabla: {result.capa2.tabla}\n"
                f"Tarea: {result.capa2.tarea}\n"
                f"Confianza: {result.combined_confidence:.0%}\n"
                f"Validación: {validity}\n\n"
                f"(Registro #{result.db_id})"
            )
        else:
            await update.message.reply_text(
                "Se detectó una posible tarea, pero no pudo clasificarse con exactitud.\n"
                f"Equipo probable: {result.capa1.equipo_probable or 'N/A'}\n"
                f"Confianza capa 1: {result.capa1.confianza:.0%}\n"
                f"Motivo: {result.capa1.motivo or 'N/A'}\n\n"
                f"(Registro #{result.db_id})"
            )

    except Exception:
        logger.exception("Error procesando mensaje chat=%s msg=%s", chat_id, message_id)
        await update.message.reply_text(
            "Ocurrió un error al procesar tu mensaje. Intenta de nuevo más tarde."
        )
