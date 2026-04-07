from __future__ import annotations

import logging

from telegram import ChatMember, Update
from telegram.ext import ContextTypes

from app.services.chat_settings_service import (
    VALID_EQUIPOS,
    clear_equipo_principal,
    get_equipo_principal,
    normalize_equipo,
    set_equipo_principal,
)
from app.services.classifier_service import Decision, process_message

logger = logging.getLogger(__name__)

_EQUIPOS_LIST_TEXT = "\n".join(f"• {e}" for e in VALID_EQUIPOS)


async def _is_group_admin(update: Update) -> bool:
    """Verifica si el usuario es admin en un grupo. Devuelve True en chats privados."""
    chat = update.effective_chat
    if chat is None or chat.type == "private":
        return True
    user = update.effective_user
    if user is None:
        return False
    try:
        member = await chat.get_member(user.id)
        return member.status in (ChatMember.ADMINISTRATOR, ChatMember.OWNER)
    except Exception:
        logger.warning("No se pudo verificar rol de admin para user=%s chat=%s", user.id, chat.id)
        return False


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    await update.message.reply_text(
        "Hola, soy el bot de registro de tareas de Rusconi Consulting.\n\n"
        "Monitoreo los mensajes del grupo y detecto automáticamente "
        "tareas registrables del catálogo del despacho.\n\n"
        "Comandos disponibles:\n"
        "/start — Mostrar este mensaje\n"
        "/registrarequipoprincipal <equipo> — Configurar equipo del chat\n"
        "/verequipo — Ver equipo actual del chat\n"
        "/eliminarequipo — Eliminar equipo del chat"
    )


async def registrar_equipo_principal_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    if not update.message or not update.effective_user:
        return

    chat_id = update.message.chat_id
    user = update.effective_user

    if not await _is_group_admin(update):
        await update.message.reply_text(
            "Solo los administradores del grupo pueden usar este comando."
        )
        return

    raw_args = " ".join(context.args) if context.args else ""
    if not raw_args.strip():
        await update.message.reply_text(
            f"Uso: /registrarequipoprincipal <equipo>\n\n"
            f"Equipos válidos:\n{_EQUIPOS_LIST_TEXT}"
        )
        return

    equipo_canonico = normalize_equipo(raw_args)
    if equipo_canonico is None:
        await update.message.reply_text(
            f"Equipo no válido: «{raw_args.strip()}»\n\n"
            f"Equipos válidos:\n{_EQUIPOS_LIST_TEXT}"
        )
        return

    try:
        await set_equipo_principal(chat_id, equipo_canonico)
    except Exception:
        logger.exception(
            "Error guardando equipo principal chat=%s user=%s equipo=%s",
            chat_id, user.id, equipo_canonico,
        )
        await update.message.reply_text("Error interno al guardar la configuración.")
        return

    logger.info(
        "Equipo principal configurado: chat=%s user=%s (%s) equipo=%s",
        chat_id, user.id, user.full_name, equipo_canonico,
    )
    await update.message.reply_text(
        f"Equipo principal configurado: {equipo_canonico}"
    )


async def ver_equipo_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    if not update.message:
        return

    chat_id = update.message.chat_id
    equipo = await get_equipo_principal(chat_id)

    if equipo:
        await update.message.reply_text(f"Equipo principal actual: {equipo}")
    else:
        await update.message.reply_text(
            "No hay equipo principal configurado en este chat."
        )


async def eliminar_equipo_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    if not update.message or not update.effective_user:
        return

    chat_id = update.message.chat_id
    user = update.effective_user

    if not await _is_group_admin(update):
        await update.message.reply_text(
            "Solo los administradores del grupo pueden usar este comando."
        )
        return

    try:
        existed = await clear_equipo_principal(chat_id)
    except Exception:
        logger.exception(
            "Error eliminando equipo principal chat=%s user=%s",
            chat_id, user.id,
        )
        await update.message.reply_text("Error interno al eliminar la configuración.")
        return

    if not existed:
        await update.message.reply_text("No hay equipo para eliminar.")
        return

    logger.info(
        "Equipo principal eliminado: chat=%s user=%s (%s)",
        chat_id, user.id, user.full_name,
    )
    await update.message.reply_text("Equipo principal eliminado.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    text = update.message.text or update.message.caption or ""
    if not text.strip():
        return

    chat_id = update.message.chat_id
    message_id = update.message.message_id

    equipo = await get_equipo_principal(chat_id)
    equipo_primordial = equipo if equipo else "No especificado"

    try:
        result = await process_message(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            equipo_primordial=equipo_primordial,
        )

        if result.decision == Decision.TASK_FOUND and result.capa2:
            lines = ["Tarea detectada"]
            if result.capa2.tarea:
                lines.append(f"Tarea que debe ser registrada: {result.capa2.tarea}")
            lines.append(f"Equipo: {result.capa2.equipo}")
            lines.append(f"Tabla: {result.capa2.tabla}")
            await update.message.reply_text("\n".join(lines))

    except Exception:
        logger.exception("Error procesando mensaje chat=%s msg=%s", chat_id, message_id)
