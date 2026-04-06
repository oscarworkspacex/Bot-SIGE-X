"""
Endpoint preparado para recibir webhooks de Telegram.

No se activa por defecto. Para usarlo en producción:
1. Configurar WEBHOOK_URL en .env
2. Registrar el webhook con Telegram: bot.set_webhook(url=WEBHOOK_URL)
3. Montar este router en la app de FastAPI
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request, Response

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/webhook")
async def telegram_webhook(request: Request) -> Response:
    """
    Recibe updates de Telegram via webhook.
    La integración con python-telegram-bot se hará cuando se active
    el modo webhook en producción.
    """
    body = await request.json()
    logger.info("Webhook recibido: %s", body)
    return Response(status_code=200)
