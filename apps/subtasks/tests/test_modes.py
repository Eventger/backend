from datetime import datetime
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from apps.events.models import Event, EventType
from apps.subtasks.models import Subtask
from django.contrib.auth.models import User


class SubtaskModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="demo",
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

    def test_subtask_can_be_created(self):
        subtask = Subtask.objects.create(
            event=self.event,
            name="Confirmar proveedor de sonido",
            target_date=timezone.make_aware(
                datetime(2026, 10, 20, 14, 0),
            ),
            estimated_hours=Decimal("2.50"),
            details="Contactar al proveedor.",
        )

        self.assertEqual(
            subtask.event,
            self.event,
        )
        self.assertEqual(
            subtask.name,
            "Confirmar proveedor de sonido",
        )
        self.assertEqual(
            subtask.estimated_hours,
            Decimal("2.50"),
        )
        self.assertEqual(
            subtask.details,
            "Contactar al proveedor.",
        )

    def test_subtask_has_pending_state_by_default(self):
        subtask = Subtask.objects.create(
            event=self.event,
            name="Reservar lugar",
            target_date=timezone.make_aware(
                datetime(2026, 10, 21, 10, 0),
            ),
            estimated_hours=Decimal("3.00"),
        )

        self.assertEqual(
            subtask.state,
            Subtask.State.PENDING,
        )

    def test_event_has_related_subtasks(self):
        subtask = Subtask.objects.create(
            event=self.event,
            name="Montar escenario",
            target_date=timezone.make_aware(
                datetime(2026, 10, 22, 8, 0),
            ),
            estimated_hours=Decimal("4.00"),
        )

        self.assertIn(
            subtask,
            self.event.subtasks.all(),
        )