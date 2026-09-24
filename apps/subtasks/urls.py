from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import EventSubtaskView, SubtaskViewSet, TodaySubtaskView

router = DefaultRouter()
router.register(
    "subtasks",
    SubtaskViewSet,
    basename="subtask",
)

urlpatterns = [
    path(
        "",
        include(router.urls),
    ),
    path(
        "events/<int:event_id>/subtasks/",
        EventSubtaskView.as_view(),
        name="event-subtask-list-create",
    ),
    path(
        "hoy/",
        TodaySubtaskView.as_view(),
        name="today-subtasks",
    ),
]