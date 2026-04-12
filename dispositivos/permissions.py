"""Custom permissions for devices."""

from __future__ import annotations

from rest_framework.permissions import BasePermission

from users.models import User


class IsCreator(BasePermission):
    """Allow only users with Creator role."""

    message = "Solo usuarios con rol Creador pueden ejecutar esta accion."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == User.Role.CREATOR)
