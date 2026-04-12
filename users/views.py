"""Views for users app."""

from __future__ import annotations

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import UserRegisterSerializer, UserSerializer


class RegisterUserView(APIView):
    """Public endpoint to register users."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        except Exception as exc:
            return Response(
                {"detail": "No se pudo registrar el usuario.", "error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class MeView(APIView):
    """Returns the authenticated user profile."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response(
                {"detail": "No se pudo obtener el perfil.", "error": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
