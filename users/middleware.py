"""JWT Authentication middleware for Django Channels WebSocket."""

from __future__ import annotations

from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from channels.middleware import BaseMiddleware
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed

User = get_user_model()


@database_sync_to_async
def get_user_from_token(token: str) -> User | None:
    """Extract and validate user from JWT token."""
    try:
        jwt_auth = JWTAuthentication()
        validated_token = jwt_auth.get_validated_token(token)
        user = jwt_auth.get_user(validated_token)
        return user
    except (InvalidToken, AuthenticationFailed):
        return None


class TokenAuthMiddleware(BaseMiddleware):
    """
    Middleware para autenticar conexiones WebSocket usando JWT.
    
    Soporta tokens JWT en:
    1. Query string: ws://host/ws/devices/id/?token=<JWT>
    2. En el futuro se pueden agregar headers si la implementación lo requiere
    """

    async def __call__(self, scope, receive, send):
        """Process the connection and set user in scope."""
        # Solo procesar WebSocket connections
        if scope["type"] == "websocket":
            # Extraer token del query string
            query_string = scope.get("query_string", b"").decode()
            token = None

            # Buscar token en query string (ej: ?token=eyJ...)
            if query_string and "token=" in query_string:
                for param in query_string.split("&"):
                    if param.startswith("token="):
                        token = param.split("=", 1)[1]
                        break

            # Intentar autenticar si hay token
            if token:
                user = await get_user_from_token(token)
                if user:
                    scope["user"] = user
                    scope["user_authenticated"] = True
                else:
                    scope["user_authenticated"] = False
            else:
                scope["user_authenticated"] = False

        await super().__call__(scope, receive, send)
