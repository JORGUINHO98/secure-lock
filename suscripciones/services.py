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
    Validate freemium lock restrictions.

    Premium users can lock without limit.
    Free users are limited by FREE_LOCKS_PER_DAY.
    """
    if has_active_premium(user):
        return True, ""

    limit = settings.FREE_LOCKS_PER_DAY
    today = timezone.localdate()
    used_locks = DeviceLockEvent.objects.filter(
        requested_by=user,
        action=DeviceLockEvent.Action.LOCK,
        created_at__date=today,
    ).count()

    if used_locks >= limit:
        return (
            False,
            f"Plan gratuito alcanzó {limit} bloqueos diarios. "
            "Activa Premium por $13.99 USD para bloqueos ilimitados de por vida.",
        )

    return True, ""