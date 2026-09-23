from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import EventTypeListView, EventViewSet


router = DefaultRouter()
router.register(
    "events",
    EventViewSet,
    basename="event",
)

urlpatterns = [
    path(
        "",
        include(router.urls),
    ),
    path(
        "event-types/",
        EventTypeListView.as_view(),
        name="event-type-list",
    ),
]