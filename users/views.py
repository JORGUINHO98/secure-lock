"""Views for users app."""

from __future__ import annotations

import logging
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import UserRegisterSerializer, UserSerializer

logger = logging.getLogger(__name__)


class RegisterUserView(APIView):
    """Public endpoint to register users with detailed error responses."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """
        Register a new user.
        
        Expected payload:
        {
            "email": "user@example.com",
            "password": "password123",
            "full_name": "John Doe",
            "role": "CREATOR"  # CREATOR or TARGET
        }
        
        Returns:
        - 201: User created successfully with JWT tokens
        - 400: Validation errors with detailed messages
        - 500: Server error
        """
        serializer = UserRegisterSerializer(data=request.data)
        
        # Validate data and handle errors explicitly
        if not serializer.is_valid():
            logger.warning(f"Registration validation failed: {serializer.errors}")
            # Return validation errors in a structured format
            return Response(
                {
                    "success": False,
                    "detail": "Falló la validación de datos",
                    "errors": serializer.errors,  # Contains field-specific errors
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        try:
            # Save the user
            user = serializer.save()
            logger.info(f"User registered successfully: {user.email}")
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            # Return user data with tokens
            response_data = {
                "success": True,
                "user": UserSerializer(user).data,
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as exc:
            logger.error(f"Unexpected error during registration: {str(exc)}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "detail": "Error inesperado al registrar usuario. Por favor intenta de nuevo.",
                    "error_code": "REGISTRATION_ERROR",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class MeView(APIView):
    """Returns the authenticated user profile."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get current authenticated user profile."""
        try:
            return Response(
                {
                    "success": True,
                    "user": UserSerializer(request.user).data,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as exc:
            logger.error(f"Error fetching user profile: {str(exc)}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "detail": "No se pudo obtener el perfil.",
                    "error_code": "PROFILE_ERROR",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
