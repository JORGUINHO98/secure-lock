"""Views for subscriptions app."""

from __future__ import annotations

from django.db import transaction
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import PREMIUM_PRICE_USD, Subscription
from .serializers import SubscriptionSerializer
from .services import has_active_premium


class SubscriptionViewSet(viewsets.ModelViewSet):
    """Manage user subscriptions."""

    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except Exception as exc:
            return Response(
                {"detail": "No se pudo crear la suscripcion.", "error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=["get"], url_path="premium-status")
    def premium_status(self, request):
        try:
            return Response(
                {"has_active_premium": has_active_premium(request.user)},
                status=status.HTTP_200_OK,
            )
        except Exception as exc:
            return Response(
                {"detail": "No se pudo validar el plan.", "error": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["post"], url_path="upgrade")
    def upgrade(self, request):
        """Actualiza la cuenta del usuario a PREMIUM de por vida."""
        try:
            with transaction.atomic():
                # 1. Cancelar cualquier suscripción activa actual para evitar el ValidationError del modelo
                active_subscriptions = Subscription.objects.filter(
                    user=request.user,
                    status=Subscription.Status.ACTIVE
                )
                for sub in active_subscriptions:
                    sub.status = Subscription.Status.CANCELED
                    sub.save(update_fields=["status", "updated_at"])

                # 2. Crear la nueva suscripción Premium de por vida (expires_at=None)
                new_premium = Subscription.objects.create(
                    user=request.user,
                    plan_type=Subscription.PlanType.PREMIUM,
                    price_usd=PREMIUM_PRICE_USD,
                    status=Subscription.Status.ACTIVE,
                    expires_at=None
                )

            return Response(
                {
                    "detail": "Cuenta actualizada a Premium exitosamente.",
                    "subscription": SubscriptionSerializer(new_premium).data
                },
                status=status.HTTP_200_OK
            )
        except Exception as exc:
            return Response(
                {"detail": "No se pudo actualizar a Premium.", "error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
