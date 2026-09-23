from apps.events.models import Event
from .models import Subtask

def create_subtask(*, event: Event, validated_data):
    return Subtask.objects.create(
        event=event, 
        **validated_data
    )