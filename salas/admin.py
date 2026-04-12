"""Admin configuration for rooms app."""

from django.contrib import admin

from .models import Room


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "admin", "invite_code", "created_at")
    search_fields = ("name", "admin__email")
    filter_horizontal = ("devices",)
