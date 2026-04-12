"""Views for devices and lock commands."""

from __future__ import annotations

from datetime import timedelta

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from suscripciones.services import can_issue_lock, has_active_premium
from users.models import User

from .models import Device, DeviceLockEvent
from .serializers import (
    DeviceLockEventSerializer,
    DeviceLockRequestSerializer,
    DeviceSerializer,
    DeviceUnlockRequestSerializer,
)
from .services import broadcast_device_event, send_fcm_device_command
from .tasks import auto_unlock_device_task


class DeviceViewSet(viewsets.ModelViewSet):
    """Device management and lock/unlock endpoints."""

    serializer_class = DeviceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        base_qs = Device.objects.select_related("owner").all()

        if user.role == User.Role.CREATOR:
            return base_qs.filter(Q(rooms__admin=user) | Q(owner=user)).distinct()
        return base_qs.filter(owner=user).distinct()

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except Exception as exc:
            return Response(
                {"detail": "No se pudo registrar el dispositivo.", "error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def perform_create(self, serializer):
        user = self.request.user
        owner = serializer.validated_data.get("owner")

        if user.role == User.Role.TARGET:
            serializer.save(owner=user)
        else:
            serializer.save(owner=owner or user)

    def perform_update(self, serializer):
        current_owner = serializer.instance.owner
        serializer.save(owner=current_owner)

    def _creator_can_control(self, user, device) -> bool:
        return bool(device.rooms.filter(admin=user).exists() or device.owner_id == user.id)

    @action(detail=True, methods=["post"], url_path="lock")
    def lock(self, request, pk=None):
        serializer = DeviceLockRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            device = self.get_object()

            if request.user.role != User.Role.CREATOR:
                return Response(
                    {"detail": "Solo el rol Creador puede bloquear dispositivos."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            if not self._creator_can_control(request.user, device):
                return Response(
                    {"detail": "No tienes permisos para bloquear este dispositivo."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            can_lock, lock_message = can_issue_lock(request.user)
            if not can_lock:
                return Response(
                    {
                        "detail": lock_message,
                        "premium_required": True,
                        "premium_price_usd": "13.00",
                    },
                    status=402,
                )

            now = timezone.now()
            duration = serializer.validated_data.get("duration_minutes")
            locked_until = now + timedelta(minutes=duration) if duration else None

            with transaction.atomic():
                device = Device.objects.select_for_update().get(pk=device.pk)
                device.is_locked = True
                device.allow_emergency_calls = serializer.validated_data["allow_emergency_calls"]
                device.locked_at = now
                device.locked_until = locked_until
                device.save(
                    update_fields=[
                        "is_locked",
                        "allow_emergency_calls",
                        "locked_at",
                        "locked_until",
                        "updated_at",
                    ]
                )

                DeviceLockEvent.objects.create(
                    device=device,
                    requested_by=request.user,
                    action=DeviceLockEvent.Action.LOCK,
                    reason=serializer.validated_data.get("reason", ""),
                    duration_minutes=duration,
                    expires_at=locked_until,
                    was_premium=has_active_premium(request.user),
                )

            if locked_until:
                auto_unlock_device_task.apply_async(args=[device.id], eta=locked_until)

            broadcast_device_event(
                device=device,
                action="LOCK",
                requested_by_id=request.user.id,
                extra={"reason": serializer.validated_data.get("reason", "")},
            )
            send_fcm_device_command(
                device=device,
                action="LOCK",
                extra_data={"reason": serializer.validated_data.get("reason", "")},
            )

            return Response(
                {
                    "detail": "Dispositivo bloqueado correctamente.",
                    "device": DeviceSerializer(device).data,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as exc:
            return Response(
                {"detail": "No se pudo bloquear el dispositivo.", "error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["post"], url_path="unlock")
    def unlock(self, request, pk=None):
        serializer = DeviceUnlockRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            device = self.get_object()
            user = request.user

            can_unlock = False
            if user.role == User.Role.CREATOR and self._creator_can_control(user, device):
                can_unlock = True
            if user.id == device.owner_id:
                can_unlock = True

            if not can_unlock:
                return Response(
                    {"detail": "No tienes permisos para desbloquear este dispositivo."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            with transaction.atomic():
                device = Device.objects.select_for_update().get(pk=device.pk)
                device.is_locked = False
                device.locked_at = None
                device.locked_until = None
                device.save(update_fields=["is_locked", "locked_at", "locked_until", "updated_at"])

                DeviceLockEvent.objects.create(
                    device=device,
                    requested_by=user,
                    action=DeviceLockEvent.Action.UNLOCK,
                    reason=serializer.validated_data.get("reason", ""),
                    was_premium=has_active_premium(user),
                )

            broadcast_device_event(
                device=device,
                action="UNLOCK",
                requested_by_id=user.id,
                extra={"reason": serializer.validated_data.get("reason", "")},
            )
            send_fcm_device_command(
                device=device,
                action="UNLOCK",
                extra_data={"reason": serializer.validated_data.get("reason", "")},
            )

            return Response(
                {
                    "detail": "Dispositivo desbloqueado correctamente.",
                    "device": DeviceSerializer(device).data,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as exc:
            return Response(
                {"detail": "No se pudo desbloquear el dispositivo.", "error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["get"], url_path="events")
    def events(self, request, pk=None):
        try:
            device = self.get_object()
            events = device.lock_events.select_related("requested_by").all()[:50]
            data = DeviceLockEventSerializer(events, many=True).data
            return Response(data, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response(
                {"detail": "No se pudieron obtener eventos.", "error": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
