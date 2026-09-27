from django.utils import timezone

from apps.events.models import Event
from .models import Subtask

def create_subtask(*, event: Event, validated_data):
    return Subtask.objects.create(
        event=event, 
        **validated_data
    )

def get_today_subtasks(*, user, status=None, event_id=None):
    now = timezone.localtime()

    today_start = now.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    tomorrow_start = today_start + timezone.timedelta(days=1)

    subtasks = Subtask.objects.filter(
        event__user=user,
    ).order_by(
        "target_date",
        "estimated_hours",
    )

    if status is not None:
        subtasks = subtasks.filter(state=status)

    if event_id is not None:
        subtasks = subtasks.filter(event_id=event_id)

    completed_subtasks = subtasks.filter(
        state=Subtask.State.COMPLETED,
    )

    pending_subtasks = subtasks.exclude(
        state=Subtask.State.COMPLETED,
    )

    return {
        "overdue": pending_subtasks.filter(
            target_date__lt=today_start,
        ),
        "today": pending_subtasks.filter(
            target_date__gte=today_start,
            target_date__lt=tomorrow_start,
        ),
        "upcoming": pending_subtasks.filter(
            target_date__gte=tomorrow_start,
        ),
        "completed": completed_subtasks,
    }