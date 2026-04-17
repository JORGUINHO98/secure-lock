"""Subscription models for freemium and lifetime access control."""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

PREMIUM_PRICE_USD = Decimal("13.99")


class Subscription(models.Model):
    """Represents a user subscription in the freemium or lifetime model."""

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
    # MODIFICACIÓN 1: Permite que expires_at esté vacío (nulo) para pagos de por vida.
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # F nulls_last pone los planes de por vida de primeros en el panel de administrador
        ordering = (models.F('expires_at').desc(nulls_last=True),)

    def clean(self):
        # MODIFICACIÓN 2: Solo verifica las fechas si expires_at NO está vacío.
        if self.expires_at and self.expires_at <= self.starts_at:
            raise ValidationError("La fecha de expiracion debe ser mayor al inicio.")

        if self.status == self.Status.ACTIVE:
            exists = Subscription.objects.filter(
                user=self.user,
                status=self.Status.ACTIVE
            ).exclude(pk=self.pk).exists()

            if exists:
                raise ValidationError("El usuario ya tiene una suscripción activa")

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
        """
        Devuelve True si la suscripción está activa.
        Si expires_at es nulo, significa que es acceso de por vida.
        """
        # Si el estado no es ACTIVO (ej. el padre canceló o pidió reembolso), devolvemos False de inmediato.
        if self.status != self.Status.ACTIVE:
            return False

        # MODIFICACIÓN 3: Si no hay fecha de expiración, ¡está activa para siempre!
        if self.expires_at is None:
            return True

        # Si sí hay una fecha de expiración, comprobamos que no haya vencido aún.
        return self.expires_at > timezone.now()

    def __str__(self) -> str:
        return f"{self.user_id} - {self.plan_type} ({self.status})"