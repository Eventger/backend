from datetime import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from apps.events.models import Event, EventType
from apps.subtasks.models import Subtask
from apps.subtasks.services import create_subtask


class CreateSubtaskServiceTests(TestCase):

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