"""Admin configuration for devices app."""

from django.contrib import admin

from .models import Device, DeviceLockEvent


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("id", "id_unico", "owner", "is_locked", "battery_level", "updated_at")
    list_filter = ("is_locked", "allow_emergency_calls", "platform")
    search_fields = ("id_unico", "owner__email", "display_name")


@admin.register(DeviceLockEvent)
class DeviceLockEventAdmin(admin.ModelAdmin):
    list_display = ("id", "device", "action", "requested_by", "was_premium", "created_at")
    list_filter = ("action", "was_premium")
    search_fields = ("device__id_unico", "requested_by__email")
