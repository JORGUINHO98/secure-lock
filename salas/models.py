"""Room models."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class Room(models.Model):
    """Group of devices controlled by a creator/admin."""

    name = models.CharField(max_length=120)
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="rooms_administered",
        on_delete=models.CASCADE,
    )
    devices = models.ManyToManyField("dispositivos.Device", related_name="rooms", blank=True)
    invite_code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)
        unique_together = ("name", "admin")

    def __str__(self) -> str:
        return f"{self.name} ({self.admin_id})"
