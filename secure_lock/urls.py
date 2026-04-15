from django.http import JsonResponse
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

def home(request):
    return JsonResponse({
        "mensaje": "API Secure Lock funcionando 🚀",
        "endpoints": [
            "/api/users/",
            "/api/dispositivos/",
            "/api/salas/",
            "/api/suscripciones/",
            "/api/auth/token/"
        ]
    })

urlpatterns = [
    path('', home),
    path("admin/", admin.site.urls),
    path("api/users/", include("users.urls")),
    path("api/dispositivos/", include("dispositivos.urls")),
    path("api/salas/", include("salas.urls")),
    path("api/suscripciones/", include("suscripciones.urls")),
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]