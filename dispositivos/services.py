"""Service helpers for lock signaling and push notifications."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from firebase_admin import credentials, initialize_app, messaging
from firebase_admin.exceptions import FirebaseError

logger = logging.getLogger(__name__)
_firebase_ready = False


def _ensure_firebase_initialized() -> bool:
    """Initialize Firebase admin SDK once."""
    global _firebase_ready
    if _firebase_ready:
        return True

    # First, try to load credentials from environment variable
    creds_json_str = os.getenv("FIREBASE_CREDENTIALS_JSON")
    if creds_json_str:
        try:
            creds_dict = json.loads(creds_json_str)
            initialize_app(credentials.Certificate(creds_dict))
            _firebase_ready = True
            return True
        except json.JSONDecodeError as exc:
            logger.error("FIREBASE_CREDENTIALS_JSON is not valid JSON: %s", exc)
            return False
        except Exception as exc:
            logger.exception("Firebase initialization from env failed: %s", exc)
            return False

    # Fallback: use credentials file path from settings
    creds_path = settings.FIREBASE_CREDENTIALS_PATH
    if not creds_path:
        logger.warning("FIREBASE_CREDENTIALS_PATH is missing and FIREBASE_CREDENTIALS_JSON env var not set. Push notifications are disabled.")
        return False

    try:
        initialize_app(credentials.Certificate(creds_path))
        _firebase_ready = True
        return True
    except ValueError:
        _firebase_ready = True
        return True
    except Exception as exc:
        logger.exception("Firebase initialization failed: %s", exc)
        return False


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
        {"type": "device.status", "payload": payload},
    )


def send_fcm_device_command(device, action: str, extra_data: dict[str, Any] | None = None):
    """Send a high-priority lock/unlock command via FCM."""
    if not device.fcm_token:
        return
    if not _ensure_firebase_initialized():
        return

    data = {
        "device_id": str(device.id),
        "id_unico": device.id_unico,
        "action": action,
        "is_locked": str(device.is_locked).lower(),
        "allow_emergency_calls": str(device.allow_emergency_calls).lower(),
        "locked_until": device.locked_until.isoformat() if device.locked_until else "",
    }
    if extra_data:
        data.update({key: str(value) for key, value in extra_data.items()})

    message = messaging.Message(
        token=device.fcm_token,
        data=data,
        android=messaging.AndroidConfig(priority="high"),
    )
    try:
        messaging.send(message)
    except FirebaseError as exc:
        logger.exception("FCM dispatch failed: %s", exc)
