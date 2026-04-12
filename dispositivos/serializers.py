"""Serializers for devices."""

from __future__ import annotations

from rest_framework import serializers

from .models import Device, DeviceLockEvent


class DeviceSerializer(serializers.ModelSerializer):
    """Serializer for target devices."""

    owner_email = serializers.EmailField(source="owner.email", read_only=True)

    class Meta:
        model = Device
        fields = (
            "id",
            "owner",
            "owner_email",
            "id_unico",
            "display_name",
            "fcm_token",
            "is_locked",
            "battery_level",
            "allow_emergency_calls",
            "locked_at",
            "locked_until",
            "platform",
            "os_version",
            "app_version",
            "technical_info",
            "last_seen",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "owner_email",
            "is_locked",
            "locked_at",
            "locked_until",
            "created_at",
            "updated_at",
        )
        extra_kwargs = {
            "owner": {"required": False},
        }

    def validate_id_unico(self, value):
        """Ensure device unique id is globally unique."""
        qs = Device.objects.filter(id_unico=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("El ID unico del dispositivo ya existe.")
        return value


class DeviceLockRequestSerializer(serializers.Serializer):
    """Input serializer for lock endpoint."""

    duration_minutes = serializers.IntegerField(min_value=1, max_value=1440, required=False)
    reason = serializers.CharField(max_length=255, required=False, allow_blank=True)
    allow_emergency_calls = serializers.BooleanField(default=True)

    def validate_allow_emergency_calls(self, value):
        if not value:
            raise serializers.ValidationError(
                "El backend exige permitir llamadas de emergencia durante el bloqueo."
            )
        return value


class DeviceUnlockRequestSerializer(serializers.Serializer):
    """Input serializer for unlock endpoint."""

    reason = serializers.CharField(max_length=255, required=False, allow_blank=True)


class DeviceLockEventSerializer(serializers.ModelSerializer):
    """Read serializer for lock events."""

    requested_by_email = serializers.EmailField(source="requested_by.email", read_only=True)

    class Meta:
        model = DeviceLockEvent
        fields = (
            "id",
            "device",
            "requested_by",
            "requested_by_email",
            "action",
            "reason",
            "duration_minutes",
            "expires_at",
            "was_premium",
            "created_at",
        )
        read_only_fields = fields
