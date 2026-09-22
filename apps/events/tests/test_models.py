from datetime import datetime

from apps.events.models import Event, EventType
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

class EventModelTests(TestCase):

    def test_event_type_can_be_created(self):
        event_type = EventType.objects.create(
            name="Conferencia",
            description="Evento académico",
        )

        self.assertEqual(event_type.name, "Conferencia")
        self.assertEqual(
            event_type.description,
            "Evento académico",
        )

    def test_event_can_be_created(self):
        user = User.objects.create_user(
            username="demo",
            password="test-password",
        )

        event_type = EventType.objects.create(
            name="Conferencia",
        )

        event = Event.objects.create(
            user=user,
            name="Conferencia de tecnología",
            type=event_type,
            date=timezone.make_aware(
                datetime(2026, 10, 15, 18, 30),
            ),
            location="Cali",
        )

        self.assertEqual(
            event.name,
            "Conferencia de tecnología",
        )
        self.assertEqual(event.user, user)
        self.assertEqual(event.type, event_type)
        self.assertEqual(event.location, "Cali")