from __future__ import annotations

import logging
from typing import Any

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


def broadcast_device_event(device, action: str, requested_by_id: int | None, extra: dict[str, Any] | None = None):
    """Emit lock state updates through Django Channels."""
    channel_layer = get_channel_layer()
    if not channel_layer:
        logger.warning("Channel layer unavailable; websocket message skipped.")
        return

    payload = {
        "device_id": device.id,
        "id_unico": device.id_unico,
        "action": action,
        "is_locked": device.is_locked,
        "allow_emergency_calls": device.allow_emergency_calls,
        "locked_until": device.locked_until.isoformat() if device.locked_until else None,
        "requested_by_id": requested_by_id,
    }

    if extra:
        payload.update(extra)

    async_to_sync(channel_layer.group_send)(
        f"device_{device.id_unico}",
        {
            "type": "device.status",
            "payload": payload,
        },
    )


def send_fcm_device_command(*args, **kwargs):
    """
    Firebase eliminado.

    Esta función se deja como placeholder para evitar errores
    si en otras partes del código aún se la está llamando.
    """
    logger.info("send_fcm_device_command() deshabilitado: Firebase no está configurado.")
    return