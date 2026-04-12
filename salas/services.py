"""Service utilities for room QR linking."""

from __future__ import annotations

import base64
import io
import json

import qrcode
from django.core import signing
from django.utils import timezone


def build_room_qr_payload(room, id_unico: str | None = None) -> dict:
    """Create signed payload for room-device linking."""
    payload = {
        "room_id": room.id,
        "room_name": room.name,
        "invite_code": str(room.invite_code),
        "generated_at": timezone.now().isoformat(),
    }
    if id_unico:
        payload["id_unico"] = id_unico

    signed_payload = signing.dumps(payload, salt="secure-lock-room-link")
    return {
        "payload": payload,
        "signed_payload": signed_payload,
    }


def generate_qr_base64(content: dict) -> str:
    """Generate base64 PNG from JSON payload for frontend QR rendering."""
    json_payload = json.dumps(content, separators=(",", ":"))
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(json_payload)
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")

    image_buffer = io.BytesIO()
    image.save(image_buffer, format="PNG")
    return base64.b64encode(image_buffer.getvalue()).decode("utf-8")
