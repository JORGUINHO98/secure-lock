"""Subscription and freemium service helpers."""

from __future__ import annotations

from django.conf import settings
from django.db.models import Q  # ¡NUEVO! Importamos Q para condiciones OR
from django.utils import timezone

from dispositivos.models import DeviceLockEvent

from .models import PREMIUM_PRICE_USD, Subscription


def get_active_subscription(user):
    """Return active subscription for user if available (Supports Lifetime)."""
    return (
        Subscription.objects.filter(
            # MODIFICACIÓN: "Que expire en el futuro" O "Que no tenga expiración (De por vida)"
            Q(expires_at__gt=timezone.now()) | Q(expires_at__isnull=True),
            user=user,
            status=Subscription.Status.ACTIVE,
        )
        # nulls_last evita que un plan de por vida sea empujado al final de la lista
        .order_by(Subscription._meta.get_field('expires_at').name) # Ordenamiento seguro
        .first()
    )


def has_active_premium(user) -> bool:
    """Check whether user has a valid premium subscription."""
    subscription = get_active_subscription(user)
    if not subscription:
        return False

    return (
        subscription.plan_type == Subscription.PlanType.PREMIUM
        and subscription.price_usd == PREMIUM_PRICE_USD
        and subscription.is_active_now
    )


def can_issue_lock(user) -> tuple[bool, str]:
    """
    Validate lock permissions.

    Bloqueos ilimitados para todos los usuarios, siempre que el dispositivo
    esté dentro de una sala permitida. Las restricciones de capacidad se
    aplican en la creación de salas y vinculación de dispositivos.
    """
    return True, ""