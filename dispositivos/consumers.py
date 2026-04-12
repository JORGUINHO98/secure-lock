"""WebSocket consumer for realtime lock state updates."""

from __future__ import annotations

from channels.generic.websocket import AsyncJsonWebsocketConsumer


class DeviceStatusConsumer(AsyncJsonWebsocketConsumer):
    """Subscribe clients to realtime updates for a specific device id_unico."""

    async def connect(self):
        self.device_unique_id = self.scope["url_route"]["kwargs"]["id_unico"]
        self.group_name = f"device_{self.device_unique_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def device_status(self, event):
        await self.send_json(event["payload"])
