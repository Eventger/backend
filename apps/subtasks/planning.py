from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.db.models.functions import TruncDate
from django.utils.formats import date_format
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError

from apps.users.models import User
from .models import Subtask


def validate_daily_limit_reduction(*, user, hours):
    """Comprueba la carga con el organizador bloqueado por la transacción de guardado."""
    if hours >= user.daily_limit_hours:
        return
    busiest = (
        Subtask.objects.filter(event__user=user)
        .exclude(state=Subtask.State.COMPLETED)
        .annotate(day=TruncDate("target_date", tzinfo=timezone.get_default_timezone()))
        .values("day")
        .annotate(total=Sum("estimated_hours"))
        .filter(total__gt=hours)
        .order_by("-total", "day")
        .first()
    )
    if busiest is not None:
        hours_label = format(busiest["total"].normalize(), "f").replace(".", ",")
        day_label = date_format(busiest["day"], "DATE_FORMAT")
        raise ValidationError({"daily_limit_hours": [
            f"Tienes {hours_label} h programadas para el {day_label}. "
            f"Usa al menos {hours_label} h o reprograma.",
        ]})


def daily_plan(*, user, subtask, target_date, estimated_hours, state=None, suggest=True):
    """Carga del organizador, en calendario de Bogotá y sin contar la gestión dos veces."""
    day = timezone.localdate(target_date)
    limit = user.daily_limit_hours
    pending = Subtask.objects.filter(event__user=user).exclude(
        state=Subtask.State.COMPLETED,
    ).exclude(pk=subtask.pk)
    tasks = list(pending.filter(target_date__date=day).select_related("event"))
    existing = sum((task.estimated_hours for task in tasks), Decimal("0"))
    candidate_state = state if state is not None else subtask.state
    added = estimated_hours if candidate_state != Subtask.State.COMPLETED else Decimal("0")
    total = existing + added
    overload = max(total - limit, Decimal("0"))
    deadline = timezone.localdate(subtask.event.date)
    result = {
        "date": day.isoformat(),
        "event_date": deadline.isoformat(),
        "existing_hours": str(existing),
        "added_hours": str(added),
        "planned_hours": str(total),
        "daily_limit_hours": str(limit),
        "overload_hours": str(overload),
        "has_conflict": overload > 0,
        # Compatibilidad con los consumidores del contrato de sobrecarga anterior.
        "limit_hours": str(limit),
        "exceeds_by": str(overload),
        "tasks": [
            {"id": task.pk, "name": task.name, "event_name": task.event.name,
             "estimated_hours": str(task.estimated_hours)} for task in tasks
        ],
        "suggestion": None,
    }
    if suggest and overload > 0 and added <= limit:
        start = max(day + timedelta(days=1), timezone.localdate())
        # Una consulta para las cargas del intervalo; la selección manual no está limitada a 30 días.
        end = min(deadline, start + timedelta(days=29))
        totals = {
            item["target_date__date"]: item["total"]
            for item in pending.filter(target_date__date__range=(start, end)).values(
                "target_date__date",
            ).annotate(total=Sum("estimated_hours"))
        }
        candidate = start
        while candidate <= end:
            candidate_total = totals.get(candidate, Decimal("0")) + added
            if candidate_total <= limit:
                result["suggestion"] = {
                    "date": candidate.isoformat(), "planned_hours": str(candidate_total),
                }
                break
            candidate += timedelta(days=1)
    return result


class SchedulingConflict(Exception):
    def __init__(self, plan):
        self.plan = plan


@transaction.atomic
def save_planning_update(*, serializer, user):
    """Vuelve a validar al guardar; serializa cambios de carga y límite por organizador."""
    organizer = User.objects.select_for_update().get(pk=user.pk)
    current = get_object_or_404(Subtask.objects.select_for_update(), pk=serializer.instance.pk, event__user=user)
    data = serializer.validated_data
    date = data.get("target_date", current.target_date)
    if (
        "target_date" in data
        and timezone.localdate(date) != timezone.localdate(current.target_date)
        and timezone.localdate(date) < timezone.localdate()
    ):
        raise ValidationError({"target_date": ["No puedes reprogramar una tarea para una fecha anterior a hoy."]})
    if "target_date" in data and timezone.localdate(date) > timezone.localdate(current.event.date):
        raise ValidationError({"target_date": ["La fecha límite no puede ser posterior a la fecha del evento."]})
    hours = data.get("estimated_hours", current.estimated_hours)
    state = data.get("state", current.state)
    changed = (
        timezone.localdate(date) != timezone.localdate(current.target_date)
        or hours != current.estimated_hours
        or (current.state == Subtask.State.COMPLETED and state != current.state)
    )
    plan = daily_plan(user=organizer, subtask=current, target_date=date, estimated_hours=hours, state=state)
    if changed and state != Subtask.State.COMPLETED and plan["has_conflict"]:
        raise SchedulingConflict(plan)
    serializer.instance = current
    return serializer.save(), plan
