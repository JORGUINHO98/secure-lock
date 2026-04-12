"""Serializers for subscriptions."""

from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from .models import PREMIUM_PRICE_USD, Subscription


class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for subscription CRUD."""

    is_active_now = serializers.BooleanField(read_only=True)

    class Meta:
        model = Subscription
        fields = (
            "id",
            "user",
            "plan_type",
            "price_usd",
            "status",
            "starts_at",
            "expires_at",
            "is_active_now",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "user", "created_at", "updated_at", "is_active_now")

    def validate(self, attrs):
        plan_type = attrs.get("plan_type")
        price_usd = attrs.get("price_usd", Decimal("0.00"))

        if plan_type == Subscription.PlanType.PREMIUM and price_usd != PREMIUM_PRICE_USD:
            raise serializers.ValidationError(
                {"price_usd": f"Premium requiere precio exacto de {PREMIUM_PRICE_USD} USD."}
            )
        return attrs
