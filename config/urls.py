from django.urls import path, include
from drf_spectacular.utils import extend_schema
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from config.api_serializers import HealthResponseSerializer, IndexResponseSerializer


@extend_schema(responses={200: HealthResponseSerializer})
@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    # Verifica el proceso HTTP, no la disponibilidad de PostgreSQL.
    return Response({"status": "ok", "service": "eventger-backend"})


@extend_schema(responses={200: IndexResponseSerializer})
@api_view(["GET"])
@permission_classes([AllowAny])
def index(request):
    return Response({"service": "Eventger API", "health": "/health/"})

urlpatterns = [
    path("", index),
    path("health/", health),
    path("api/schema/", 
        SpectacularAPIView.as_view(), 
        name="schema"),
    path("api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("", include("apps.events.urls")),
    path("", include("apps.subtasks.urls")),
]
