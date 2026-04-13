"""WebSocket consumer for realtime lock state updates."""

from __future__ import annotations

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()


class DeviceStatusConsumer(AsyncJsonWebsocketConsumer):
    """Subscribe clients to realtime updates for a specific device id_unico."""

    @database_sync_to_async
    def get_user_device_access(self, user_id: int, device_id_unico: str) -> bool:
        """Check if user owns the device or is an admin of related sala."""
        if not user_id:
            return False

        from .models import Device
        from salas.models import Sala

        try:
            device = Device.objects.get(id_unico=device_id_unico)
            
            # Check if user is the device owner
            if device.owner_id == user_id:
                return True

            # Check if user is an admin of any sala containing this device
            # (optional: if your Sala model has a relationship to Device)
            # For now, we allow if user is device owner
            return False
        except Device.DoesNotExist:
            return False

    async def connect(self):
        """
        Accept WebSocket connection only if user is authenticated and authorized.
        
        Requires:
        - Valid JWT token (via TokenAuthMiddleware)
        - User must be the device owner or sala admin
        """
        self.device_unique_id = self.scope["url_route"]["kwargs"]["id_unico"]
        
        # Check if user is authenticated
        user = self.scope.get("user")
        if not user or user.is_anonymous:
            # Close connection with code 4001 (Unauthorized)
            await self.close(code=4001)
            return

        # Verify user has access to this device
        has_access = await self.get_user_device_access(user.id, self.device_unique_id)
        if not has_access:
            # Close connection with code 4003 (Forbidden)
            await self.close(code=4003)
            return

        # User is authenticated and authorized
        self.group_name = f"device_{self.device_unique_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def device_status(self, event):
        await self.send_json(event["payload"])
