"""Serializers for rooms and linking."""

from __future__ import annotations

from rest_framework import serializers

from django.conf import settings
from dispositivos.models import Device
from suscripciones.services import has_active_premium
from users.models import User

from .models import Room


class RoomSerializer(serializers.ModelSerializer):
    """Serializer for rooms."""

    device_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Device.objects.all(),
        source="devices",
        required=False,
        write_only=True,
    )
    devices = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Room
        fields = (
            "id",
            "name",
            "admin",
            "devices",
            "device_ids",
            "invite_code",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "admin", "invite_code", "created_at", "updated_at")

    def get_devices(self, obj):
        return [
            {
                "id": device.id,
                "id_unico": device.id_unico,
                "display_name": device.display_name,
                "is_locked": device.is_locked,
            }
            for device in obj.devices.all()
        ]

    def validate(self, attrs):
        user = self.context["request"].user
        if user.role != User.Role.CREATOR:
            raise serializers.ValidationError("Solo usuarios Creador pueden administrar salas.")
        
        # Verificar límites de salas para usuarios gratuitos
        if not has_active_premium(user):
            existing_rooms = Room.objects.filter(admin=user).count()
            if existing_rooms >= settings.MAX_FREE_ROOMS:
                raise serializers.ValidationError(
                    f"Plan gratuito limitado a {settings.MAX_FREE_ROOMS} salas. "
                    "Activa Premium por $13.99 USD para salas ilimitadas."
                )
        
        return attrs

    def create(self, validated_data):
        devices = validated_data.pop("devices", [])
        room = Room.objects.create(admin=self.context["request"].user, **validated_data)
        if devices:
            room.devices.set(devices)
        return room

    def update(self, instance, validated_data):
        devices = validated_data.pop("devices", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        if devices is not None:
            instance.devices.set(devices)
        return instance


class LinkDeviceSerializer(serializers.Serializer):
    """Serializer to link a device to a room using QR invite code."""

    invite_code = serializers.UUIDField()
    id_unico = serializers.CharField(max_length=140, required=False)
    unique_id = serializers.CharField(max_length=140, required=False, write_only=True)

    def validate(self, attrs):
        id_unico = attrs.get("id_unico") or attrs.get("unique_id")
        if not id_unico:
            raise serializers.ValidationError({"id_unico": "Debes enviar id_unico o unique_id."})
        attrs["id_unico"] = id_unico
        
        invite_code = attrs.get("invite_code")
        try:
            self.sala = Room.objects.get(invite_code=invite_code)
        except Room.DoesNotExist:
            raise serializers.ValidationError({"invite_code": "La sala con este código no existe."})
            
        return attrs
