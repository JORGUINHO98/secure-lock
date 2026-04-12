"""WebSocket routing for devices."""

from django.urls import re_path

from .consumers import DeviceStatusConsumer

websocket_urlpatterns = [
    re_path(
        r"^ws/devices/(?P<id_unico>[-\w]+)/$",
        DeviceStatusConsumer.as_asgi(),
    ),
]
