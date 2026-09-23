from django.urls import path
from .views import SubtaskCreateView

urlpatterns = [
    path("events/<int:event_id>/subtasks/", 
    SubtaskCreateView.as_view(), 
    name="subtask-create"),
]