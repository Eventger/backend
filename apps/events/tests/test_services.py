from datetime import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from apps.events.models import Event, EventType
from apps.events.services import create_event


class CreateEventServiceTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="demo",
            password="test-password",
        )

        self.event_type = EventType.objects.create(
            name="Conferencia",
        )

    def test_create_event(self):
        validated_data = {
            "name": "Conferencia de tecnología",
            "type": self.event_type,
            "date": timezone.make_aware(
                datetime(2026, 10, 15, 18, 30),
            ),
            "location": "Cali",
        }

        event = create_event(
            validated_data=validated_data,
        )

        self.assertIsInstance(event, Event)
        self.assertEqual(
            event.name,
            "Conferencia de tecnología",
        )
        self.assertEqual(
            event.type,
            self.event_type,
        )
        self.assertEqual(
            event.location,
            "Cali",
        )

    def test_create_event_assigns_demo_user(self):
        validated_data = {
            "name": "Evento de prueba",
            "type": self.event_type,
            "date": timezone.make_aware(
                datetime(2026, 11, 1, 10, 0),
            ),
            "location": "Bogotá",
        }

        event = create_event(
            validated_data=validated_data,
        )

        self.assertEqual(event.user, self.user)

    def test_create_event_persists_event(self):
        validated_data = {
            "name": "Evento persistente",
            "type": self.event_type,
            "date": timezone.make_aware(
                datetime(2026, 12, 5, 14, 0),
            ),
            "location": "Medellín",
        }

        event = create_event(
            validated_data=validated_data,
        )

        self.assertTrue(
            Event.objects.filter(
                id=event.id,
            ).exists()
        )

    def test_create_event_fails_if_demo_user_does_not_exist(self):
        self.user.delete()

        validated_data = {
            "name": "Evento sin usuario",
            "type": self.event_type,
            "date": timezone.make_aware(
                datetime(2026, 12, 10, 10, 0),
            ),
            "location": "Cali",
        }

        with self.assertRaises(User.DoesNotExist):
            create_event(
                validated_data=validated_data,
            )