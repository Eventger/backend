from datetime import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.events.models import Event, EventType
from apps.events.services import create_event

User = get_user_model()


class CreateEventServiceTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="event-owner",
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
            user=self.user,
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
            user=self.user,
            validated_data=validated_data,
        )

        self.assertTrue(
            Event.objects.filter(
                id=event.id,
            ).exists()
        )
