"""Views for room management and QR linking."""

from __future__ import annotations

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from dispositivos.models import Device
from suscripciones.services import has_active_premium
from users.models import User

from .models import Room
from .serializers import LinkDeviceSerializer, RoomSerializer
from .services import build_room_qr_payload, generate_qr_base64


class RoomViewSet(viewsets.ModelViewSet):
    """Manage creator rooms and device linking."""

    serializer_class = RoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.CREATOR:
            return Room.objects.filter(admin=user).prefetch_related("devices")
        return Room.objects.filter(devices__owner=user).prefetch_related("devices").distinct()

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except Exception as exc:
            return Response(
                {"detail": "No se pudo crear la sala.", "error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def _ensure_room_admin(self, room, user) -> bool:
        return bool(user.role == User.Role.CREATOR and room.admin_id == user.id)

    def update(self, request, *args, **kwargs):
        room = self.get_object()
        if not self._ensure_room_admin(room, request.user):
            return Response(
                {"detail": "Solo el administrador de la sala puede editarla."},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            return super().update(request, *args, **kwargs)
        except Exception as exc:
            return Response(
                {"detail": "No se pudo actualizar la sala.", "error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def partial_update(self, request, *args, **kwargs):
        room = self.get_object()
        if not self._ensure_room_admin(room, request.user):
            return Response(
                {"detail": "Solo el administrador de la sala puede editarla."},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            return super().partial_update(request, *args, **kwargs)
        except Exception as exc:
            return Response(
                {"detail": "No se pudo actualizar la sala.", "error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def destroy(self, request, *args, **kwargs):
        room = self.get_object()
        if not self._ensure_room_admin(room, request.user):
            return Response(
                {"detail": "Solo el administrador de la sala puede eliminarla."},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            return super().destroy(request, *args, **kwargs)
        except Exception as exc:
            return Response(
                {"detail": "No se pudo eliminar la sala.", "error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["get"], url_path="qr")
    def qr(self, request, pk=None):
        try:
            room = self.get_object()
            if not self._ensure_room_admin(room, request.user):
                return Response(
                    {"detail": "Solo el administrador de la sala puede generar el QR."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            id_unico = request.query_params.get("id_unico")
            qr_data = build_room_qr_payload(room, id_unico=id_unico)
            qr_image_b64 = generate_qr_base64(qr_data["payload"])

            return Response(
                {
                    "room_id": room.id,
                    "invite_code": str(room.invite_code),
                    "signed_payload": qr_data["signed_payload"],
                    "qr_base64": qr_image_b64,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as exc:
            return Response(
                {"detail": "No se pudo generar el QR.", "error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=["post"], url_path="link-device")
    def link_device(self, request):
        serializer = LinkDeviceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            room = get_object_or_404(Room, invite_code=serializer.validated_data["invite_code"])
            device = get_object_or_404(Device, id_unico=serializer.validated_data["id_unico"])
            user = request.user

            if user.role == User.Role.CREATOR and room.admin_id != user.id:
                return Response(
                    {"detail": "Solo el administrador de la sala puede vincular desde este usuario."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            if user.role == User.Role.TARGET and device.owner_id != user.id:
                return Response(
                    {"detail": "Solo puedes vincular tus propios dispositivos."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            # Verificar límites de dispositivos para usuarios gratuitos
            if not has_active_premium(room.admin):
                if room.devices.count() >= settings.MAX_FREE_DEVICES_PER_ROOM:
                    return Response(
                        {
                            "detail": f"Plan gratuito limitado a {settings.MAX_FREE_DEVICES_PER_ROOM} dispositivos por sala. "
                            "Activa Premium por $13.99 USD para dispositivos ilimitados."
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )

            room.devices.add(device)
            return Response(
                {
                    "detail": "Dispositivo vinculado correctamente.",
                    "room": RoomSerializer(room, context={"request": request}).data,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as exc:
            return Response(
                {"detail": "No se pudo vincular el dispositivo.", "error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
