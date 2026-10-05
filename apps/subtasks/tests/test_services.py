from datetime import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.events.models import Event, EventType
from apps.subtasks.models import Subtask
from apps.subtasks.services import ( check_daily_overload, create_subtask, get_daily_planned_hours,)

User = get_user_model()


class CreateSubtaskServiceTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="task-owner",
            password="test-password",
        )

        self.event_type = EventType.objects.create(
            name="Conferencia",
        )

        self.event = Event.objects.create(
            user=self.user,
            name="Conferencia de tecnología",
            type=self.event_type,
            date=timezone.make_aware(
                datetime(2026, 10, 15, 18, 30),
            ),
            location="Cali",
        )

    def test_create_subtask(self):
        validated_data = {
            "name": "Confirmar proveedor de sonido",
            "target_date": timezone.make_aware(
                datetime(2026, 10, 20, 14, 0),
            ),
            "estimated_hours": Decimal("2.50"),
            "details": "Contactar al proveedor.",
        }

        subtask = create_subtask(
            event=self.event,
            validated_data=validated_data,
        )

        self.assertIsInstance(
            subtask,
            Subtask,
        )

        self.assertEqual(
            subtask.name,
            "Confirmar proveedor de sonido",
        )

        self.assertEqual(
            subtask.event,
            self.event,
        )

    def test_create_subtask_assigns_pending_state(self):
        validated_data = {
            "name": "Reservar lugar",
            "target_date": timezone.make_aware(
                datetime(2026, 10, 21, 10, 0),
            ),
            "estimated_hours": Decimal("3.00"),
        }

        subtask = create_subtask(
            event=self.event,
            validated_data=validated_data,
        )

        self.assertEqual(
            subtask.state,
            Subtask.State.PENDING,
        )

    def test_create_subtask_persists_subtask(self):
        validated_data = {
            "name": "Montar escenario",
            "target_date": timezone.make_aware(
                datetime(2026, 10, 22, 8, 0),
            ),
            "estimated_hours": Decimal("4.00"),
        }

        subtask = create_subtask(
            event=self.event,
            validated_data=validated_data,
        )

        self.assertTrue(
            Subtask.objects.filter(
                id=subtask.id,
                event=self.event,
            ).exists()
        )

class DailyPlanningServiceTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="planning-owner",
            password="test-password",
            daily_limit_hours=Decimal("6.00"),
        )

        self.event_type = EventType.objects.create(
            name="Conferencia",
        )

        self.event = Event.objects.create(
            user=self.user,
            name="Conferencia de tecnología",
            type=self.event_type,
            date=timezone.make_aware(
                datetime(2026, 10, 25, 18, 30),
            ),
            location="Cali",
        )

        self.target_date = timezone.make_aware(
            datetime(2026, 10, 20, 14, 0),
        )

    def test_get_daily_planned_hours_returns_zero_when_day_is_empty(self):
        result = get_daily_planned_hours(
            user=self.user,
            target_date=self.target_date,
        )

        self.assertEqual(
            result,
            Decimal("0.00"),
        )

    def test_get_daily_planned_hours_sums_pending_subtasks(self):
        Subtask.objects.create(
            event=self.event,
            name="Tarea 1",
            target_date=self.target_date,
            estimated_hours=Decimal("2.00"),
        )

        Subtask.objects.create(
            event=self.event,
            name="Tarea 2",
            target_date=self.target_date + timezone.timedelta(hours=2),
            estimated_hours=Decimal("3.00"),
        )

        result = get_daily_planned_hours(
            user=self.user,
            target_date=self.target_date,
        )

        self.assertEqual(
            result,
            Decimal("5.00"),
        )

    def test_get_daily_planned_hours_excludes_completed_subtasks(self):
        Subtask.objects.create(
            event=self.event,
            name="Pendiente",
            target_date=self.target_date,
            estimated_hours=Decimal("3.00"),
        )

        Subtask.objects.create(
            event=self.event,
            name="Completada",
            target_date=self.target_date,
            estimated_hours=Decimal("2.00"),
            state=Subtask.State.COMPLETED,
        )

        result = get_daily_planned_hours(
            user=self.user,
            target_date=self.target_date,
        )

        self.assertEqual(
            result,
            Decimal("3.00"),
        )

    def test_get_daily_planned_hours_excludes_selected_subtask(self):
        subtask = Subtask.objects.create(
            event=self.event,
            name="Tarea que se está modificando",
            target_date=self.target_date,
            estimated_hours=Decimal("2.00"),
        )

        Subtask.objects.create(
            event=self.event,
            name="Otra tarea",
            target_date=self.target_date,
            estimated_hours=Decimal("3.00"),
        )

        result = get_daily_planned_hours(
            user=self.user,
            target_date=self.target_date,
            exclude_subtask_id=subtask.id,
        )

        self.assertEqual(
            result,
            Decimal("3.00"),
        )

    def test_get_daily_planned_hours_does_not_include_other_users(self):
        other_user = User.objects.create_user(
            username="other-user",
            password="test-password",
        )

        other_event = Event.objects.create(
            user=other_user,
            name="Otro evento",
            type=self.event_type,
            date=timezone.now(),
            location="Cali",
        )

        Subtask.objects.create(
            event=self.event,
            name="Mi tarea",
            target_date=self.target_date,
            estimated_hours=Decimal("2.00"),
        )

        Subtask.objects.create(
            event=other_event,
            name="Tarea ajena",
            target_date=self.target_date,
            estimated_hours=Decimal("4.00"),
        )

        result = get_daily_planned_hours(
            user=self.user,
            target_date=self.target_date,
        )

        self.assertEqual(
            result,
            Decimal("2.00"),
        )
    def test_check_daily_overload_detects_conflict(self):
        Subtask.objects.create(
            event=self.event,
            name="Trabajo existente",
            target_date=self.target_date,
            estimated_hours=Decimal("5.00"),
        )

        subtask = Subtask.objects.create(
            event=self.event,
            name="Tarea a mover",
            target_date=self.target_date + timezone.timedelta(days=1),
            estimated_hours=Decimal("2.00"),
        )

        result = check_daily_overload(
            user=self.user,
            subtask=subtask,
            target_date=self.target_date,
        )

        self.assertTrue(
            result["has_conflict"],
        )

        self.assertEqual(
            result["planned_hours"],
            Decimal("7.00"),
        )

        self.assertEqual(
            result["limit_hours"],
            Decimal("6.00"),
        )

        self.assertEqual(
            result["exceeds_by"],
            Decimal("1.00"),
        )
    def test_check_daily_overload_allows_exact_daily_limit(self):
        Subtask.objects.create(
            event=self.event,
            name="Trabajo existente",
            target_date=self.target_date,
            estimated_hours=Decimal("4.00"),
        )

        subtask = Subtask.objects.create(
            event=self.event,
            name="Tarea a mover",
            target_date=self.target_date + timezone.timedelta(days=1),
            estimated_hours=Decimal("2.00"),
        )

        result = check_daily_overload(
            user=self.user,
            subtask=subtask,
            target_date=self.target_date,
        )

        self.assertFalse(
            result["has_conflict"],
        )

        self.assertEqual(
            result["planned_hours"],
            Decimal("6.00"),
        )

        self.assertEqual(
            result["exceeds_by"],
            Decimal("0.00"),
        )
    def test_check_daily_overload_uses_user_daily_limit(self):
        self.user.daily_limit_hours = Decimal("8.00")
        self.user.save()

        Subtask.objects.create(
            event=self.event,
            name="Trabajo existente",
            target_date=self.target_date,
            estimated_hours=Decimal("5.00"),
        )

        subtask = Subtask.objects.create(
            event=self.event,
            name="Tarea a mover",
            target_date=self.target_date + timezone.timedelta(days=1),
            estimated_hours=Decimal("2.00"),
        )

        result = check_daily_overload(
            user=self.user,
            subtask=subtask,
            target_date=self.target_date,
        )

        self.assertFalse(
            result["has_conflict"],
        )

        self.assertEqual(
            result["planned_hours"],
            Decimal("7.00"),
        )

        self.assertEqual(
            result["limit_hours"],
            Decimal("8.00"),
        )
    def test_check_daily_overload_can_be_resolved_by_reducing_hours(self):
        Subtask.objects.create(
            event=self.event,
            name="Trabajo existente",
            target_date=self.target_date,
            estimated_hours=Decimal("5.00"),
        )

        subtask = Subtask.objects.create(
            event=self.event,
            name="Tarea a mover",
            target_date=self.target_date + timezone.timedelta(days=1),
            estimated_hours=Decimal("2.00"),
        )

        result = check_daily_overload(
            user=self.user,
            subtask=subtask,
            target_date=self.target_date,
            estimated_hours=Decimal("1.00"),
        )

        self.assertFalse(
            result["has_conflict"],
        )

        self.assertEqual(
            result["planned_hours"],
            Decimal("6.00"),
        )
    def test_check_daily_overload_remains_when_reduction_is_not_enough(self):
        Subtask.objects.create(
            event=self.event,
            name="Trabajo existente",
            target_date=self.target_date,
            estimated_hours=Decimal("5.00"),
        )

        subtask = Subtask.objects.create(
            event=self.event,
            name="Tarea a mover",
            target_date=self.target_date + timezone.timedelta(days=1),
            estimated_hours=Decimal("3.00"),
        )

        result = check_daily_overload(
            user=self.user,
            subtask=subtask,
            target_date=self.target_date,
            estimated_hours=Decimal("2.00"),
        )

        self.assertTrue(
            result["has_conflict"],
        )

        self.assertEqual(
            result["planned_hours"],
            Decimal("7.00"),
        )

        self.assertEqual(
            result["exceeds_by"],
            Decimal("1.00"),
        )
    def test_completed_subtask_does_not_add_hours_to_planned_total(self):
        Subtask.objects.create(
            event=self.event,
            name="Trabajo existente",
            target_date=self.target_date,
            estimated_hours=Decimal("5.00"),
        )

        subtask = Subtask.objects.create(
            event=self.event,
            name="Tarea",
            target_date=self.target_date,
            estimated_hours=Decimal("2.00"),
        )

        result = check_daily_overload(
            user=self.user,
            subtask=subtask,
            state=Subtask.State.COMPLETED,
        )

        self.assertFalse(
            result["has_conflict"],
        )

        self.assertEqual(
            result["planned_hours"],
            Decimal("5.00"),
        )