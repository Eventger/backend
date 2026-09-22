from django.http import JsonResponse
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.views.decorators.http import require_safe

@require_safe
def health(request):
    # Verifica el proceso HTTP, no la disponibilidad de PostgreSQL.
    return JsonResponse({"status": "ok", "service": "eventger-backend"})

@require_safe
def index(request):
    return JsonResponse({"service": "Eventger API", "health": "/health/"})

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
]