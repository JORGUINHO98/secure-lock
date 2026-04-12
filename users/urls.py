"""URL routes for users app."""

from django.urls import path

from .views import MeView, RegisterUserView

urlpatterns = [
    path("register/", RegisterUserView.as_view(), name="register-user"),
    path("me/", MeView.as_view(), name="me"),
]
