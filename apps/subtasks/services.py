from django.utils import timezone

from apps.events.models import Event
from .models import Subtask
from decimal import Decimal
from django.db.models import Sum
from django.db import transaction
from apps.users.models import User

@transaction.atomic
def create_subtask(*, event: Event, validated_data):
    if event.user_id is not None:
        User.objects.select_for_update().get(pk=event.user_id)
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
    ).select_related("event").order_by(
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

def get_daily_planned_hours(
    *,
    user,
    target_date,
    exclude_subtask_id=None,
):
    """
    Calcula las horas planificadas de un usuario
    para el día correspondiente a target_date.

    Las subtareas COMPLETED no cuentan.
    """

    local_date = timezone.localtime(target_date)

    day_start = local_date.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    day_end = day_start + timezone.timedelta(days=1)

    subtasks = Subtask.objects.filter(
        event__user=user,
        target_date__gte=day_start,
        target_date__lt=day_end,
    ).exclude(
        state=Subtask.State.COMPLETED,
    )

    if exclude_subtask_id is not None:
        subtasks = subtasks.exclude(
            id=exclude_subtask_id,
        )

    total = subtasks.aggregate(
        total=Sum("estimated_hours"),
    )["total"]

    return total or Decimal("0.00")

def check_daily_overload(
    *,
    user,
    subtask,
    target_date=None,
    estimated_hours=None,
    state=None,
):
    """
    Simula cómo quedaría la carga diaria después
    de actualizar una subtarea.
    """

    new_target_date = (
        target_date
        if target_date is not None
        else subtask.target_date
    )

    new_estimated_hours = (
        estimated_hours
        if estimated_hours is not None
        else subtask.estimated_hours
    )

    new_state = (
        state
        if state is not None
        else subtask.state
    )

    existing_hours = get_daily_planned_hours(
        user=user,
        target_date=new_target_date,
        exclude_subtask_id=subtask.id,
    )

    if new_state == Subtask.State.COMPLETED:
        subtask_hours = Decimal("0.00")
    else:
        subtask_hours = new_estimated_hours

    planned_hours = (
        existing_hours
        + subtask_hours
    )

    limit_hours = user.daily_limit_hours

    exceeds_by = max(
        planned_hours - limit_hours,
        Decimal("0.00"),
    )

    return {
        "has_conflict": planned_hours > limit_hours,
        "planned_hours": planned_hours,
        "limit_hours": limit_hours,
        "exceeds_by": exceeds_by,
    }
