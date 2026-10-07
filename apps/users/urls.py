from django.urls import path

from apps.users.views import MeView, PlanningPreferencesView


urlpatterns = [
    path("me/", MeView.as_view(), name="me"),
    path("preferences/", PlanningPreferencesView.as_view(), name="planning-preferences"),
]
