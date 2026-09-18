from django.http import JsonResponse
from django.urls import path
from django.views.decorators.http import require_safe

@require_safe
def health(request):
    # Verifica el proceso HTTP, no la disponibilidad de PostgreSQL.
    return JsonResponse({"status": "ok", "service": "eventger-backend"})

@require_safe
def index(request):
    return JsonResponse({"service": "Eventger API", "health": "/health/"})

urlpatterns = [path("", index), path("health/", health)]
