"""Views for subscriptions app."""

from __future__ import annotations

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Subscription
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
