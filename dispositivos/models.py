"""Device models."""

from __future__ import annotations

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class Device(models.Model):
    """Represents a target device that can be remotely locked."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="devices",
        on_delete=models.CASCADE,
    )
    id_unico = models.CharField(max_length=140, unique=True, db_index=True)
    display_name = models.CharField(max_length=140)
    fcm_token = models.TextField(blank=True)
    is_locked = models.BooleanField(default=False)
    battery_level = models.PositiveSmallIntegerField(
        default=100,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    allow_emergency_calls = models.BooleanField(default=True)
    locked_at = models.DateTimeField(null=True, blank=True)
    locked_until = models.DateTimeField(null=True, blank=True)
    platform = models.CharField(max_length=60, blank=True)
    os_version = models.CharField(max_length=60, blank=True)
    app_version = models.CharField(max_length=60, blank=True)
    technical_info = models.JSONField(default=dict, blank=True)
    last_seen = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at",)

    def __str__(self) -> str:
        return f"{self.id_unico} ({'LOCKED' if self.is_locked else 'UNLOCKED'})"


class DeviceLockEvent(models.Model):
    """Audit trail for lock/unlock actions."""

    class Action(models.TextChoices):
        LOCK = "LOCK", "Lock"
        UNLOCK = "UNLOCK", "Unlock"
        AUTO_UNLOCK = "AUTO_UNLOCK", "Auto Unlock"

    device = models.ForeignKey(Device, related_name="lock_events", on_delete=models.CASCADE)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="lock_events",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    action = models.CharField(max_length=20, choices=Action.choices)
    reason = models.CharField(max_length=255, blank=True)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    was_premium = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.device_id} - {self.action} at {self.created_at}"
