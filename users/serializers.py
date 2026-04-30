"""Serializers for users app."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.validators import EmailValidator
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Read serializer for users."""

    class Meta:
        model = User
        fields = ("id", "email", "full_name", "role", "date_joined")
        read_only_fields = fields


class UserRegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration with enhanced validation."""

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text="Mínimo 8 caracteres"
    )
    email = serializers.EmailField(required=True)
    role = serializers.ChoiceField(
        choices=["CREATOR", "TARGET"],
        required=True,
        help_text="CREATOR o TARGET"
    )

    class Meta:
        model = User
        fields = ("id", "email", "full_name", "role", "password")
        read_only_fields = ("id",)

    def validate_email(self, value):
        """Validate email format and uniqueness."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Este email ya está registrado. Usa otro email o inicia sesión."
            )
        # Validar formato de email
        validator = EmailValidator()
        try:
            validator(value)
        except Exception as exc:
            raise serializers.ValidationError(f"Email inválido: {str(exc)}")
        return value.lower()

    def validate_password(self, value):
        """Validate password strength."""
        if len(value) < 8:
            raise serializers.ValidationError("La contraseña debe tener mínimo 8 caracteres.")
        if value.isdigit():
            raise serializers.ValidationError("La contraseña no puede ser solo números.")
        if value.isalpha():
            raise serializers.ValidationError("La contraseña debe contener números y letras.")
        return value

    def validate_full_name(self, value):
        """Validate full name."""
        if value and len(value) < 2:
            raise serializers.ValidationError("El nombre debe tener mínimo 2 caracteres.")
        return value.strip() if value else ""

    def validate_role(self, value):
        """Validate role is valid."""
        if value not in ["CREATOR", "TARGET"]:
            raise serializers.ValidationError(
                f"Role inválido. Debe ser 'CREATOR' o 'TARGET'. Recibido: {value}"
            )
        return value

    def create(self, validated_data):
        """Create user with validated data."""
        try:
            return User.objects.create_user(**validated_data)
        except Exception as exc:
            raise serializers.ValidationError(f"Error al crear usuario: {str(exc)}")
