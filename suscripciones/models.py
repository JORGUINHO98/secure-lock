"""Subscription models for freemium access control."""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

PREMIUM_PRICE_USD = Decimal("13.00")


class Subscription(models.Model):
    """Represents a user subscription in the freemium model."""

    class PlanType(models.TextChoices):
        FREE = "FREE", "Free"
        PREMIUM = "PREMIUM", "Premium"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Activa"
        CANCELED = "CANCELED", "Cancelada"
        EXPIRED = "EXPIRED", "Expirada"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="subscriptions",
        on_delete=models.CASCADE,
    )
    plan_type = models.CharField(max_length=20, choices=PlanType.choices, default=PlanType.FREE)
    price_usd = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    starts_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-expires_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("user",),
                condition=Q(status="ACTIVE"),
                name="unique_active_subscription_per_user",
            )
        ]

    def clean(self):
        if self.expires_at <= self.starts_at:
            raise ValidationError("La fecha de expiracion debe ser mayor al inicio.")

        if self.plan_type == self.PlanType.PREMIUM:
            if self.price_usd != PREMIUM_PRICE_USD:
                raise ValidationError(
                    {
                        "price_usd": (
                            f"El Plan Premium debe tener precio exacto de {PREMIUM_PRICE_USD} USD."
                        )
                    }
                )
        else:
            self.price_usd = Decimal("0.00")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_active_now(self) -> bool:
        return self.status == self.Status.ACTIVE and self.expires_at > timezone.now()

    def __str__(self) -> str:
        return f"{self.user_id} - {self.plan_type} ({self.status})"
