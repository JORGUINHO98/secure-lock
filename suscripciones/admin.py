"""Admin configuration for subscriptions app."""

from django.contrib import admin

from .models import Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "plan_type", "price_usd", "status", "expires_at")
    list_filter = ("plan_type", "status")
    search_fields = ("user__email",)
