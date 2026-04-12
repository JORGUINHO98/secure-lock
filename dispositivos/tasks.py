"""Celery tasks for devices."""

from __future__ import annotations

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from .models import Device, DeviceLockEvent
from .services import broadcast_device_event, send_fcm_device_command


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def auto_unlock_device_task(self, device_id: int):
    """Unlock a device automatically once the lock timer expires."""
    try:
        with transaction.atomic():
            device = Device.objects.select_for_update().get(pk=device_id)
            if not device.is_locked:
                return f"Device {device_id} already unlocked."

            if device.locked_until and timezone.now() < device.locked_until:
                return f"Device {device_id} lock window still active."

            device.is_locked = False
            device.locked_at = None
            device.locked_until = None
            device.save(update_fields=["is_locked", "locked_at", "locked_until", "updated_at"])

            DeviceLockEvent.objects.create(
                device=device,
                action=DeviceLockEvent.Action.AUTO_UNLOCK,
                reason="Timer expiration",
            )

        broadcast_device_event(device=device, action="AUTO_UNLOCK", requested_by_id=None)
        send_fcm_device_command(device=device, action="AUTO_UNLOCK")
        return f"Device {device_id} unlocked by timer."
    except Device.DoesNotExist:
        return f"Device {device_id} not found."
    except Exception as exc:
        raise self.retry(exc=exc)
