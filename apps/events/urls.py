from django.urls import path
from .views import EventCreateView, EventTypeListView

urlpatterns = [
    path("events/", EventCreateView.as_view(), name="event-create"),
    path("event-types/", EventTypeListView.as_view(), name="event-type-list"),
]