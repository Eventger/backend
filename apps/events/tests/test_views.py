from datetime import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.events.models import Event, EventType


class EventCreateViewTests(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username="demo",
            password="test-password",
        )

        self.event_type = EventType.objects.create(
            name="Conferencia",
        )

    def test_create_event_returns_201(self):
        data = {
            "name": "Conferencia de tecnología",
            "type": self.event_type.id,
            "date": "2026-10-15T18:30:00-05:00",
            "location": "Cali",
        }

        response = self.client.post(
            "/events/",
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        response_data = response.json()

        self.assertTrue(
            response_data["success"]
        )

        self.assertEqual(
            response_data["message"],
            "Evento creado correctamente.",
        )

        self.assertIn(
            "data",
            response_data,
        )

        event_data = response_data["data"]

        self.assertEqual(
            event_data["name"],
            "Conferencia de tecnología",
        )

        self.assertEqual(
            event_data["type"],
            self.event_type.id,
        )

        self.assertEqual(
            event_data["location"],
            "Cali",
        )

        self.assertEqual(
            event_data["user"],
            self.user.id,
        )

        self.assertTrue(
            Event.objects.filter(
                name="Conferencia de tecnología",
            ).exists()
        )

    def test_create_event_returns_400_when_required_fields_are_missing(self):
        response = self.client.post(
            "/events/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        response_data = response.json()

        self.assertFalse(
            response_data["success"]
        )

        self.assertIn(
            "errors",
            response_data,
        )

        self.assertIn(
            "name",
            response_data["errors"],
        )

        self.assertIn(
            "type",
            response_data["errors"],
        )

        self.assertIn(
            "date",
            response_data["errors"],
        )

        self.assertIn(
            "location",
            response_data["errors"],
        )

        self.assertEqual(
            Event.objects.count(),
            0,
        )

    def test_create_event_rejects_blank_name(self):
        data = {
            "name": "   ",
            "type": self.event_type.id,
            "date": "2026-10-15T18:30:00-05:00",
            "location": "Cali",
        }

        response = self.client.post(
            "/events/",
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        response_data = response.json()

        self.assertIn(
            "name",
            response_data["errors"],
        )

        self.assertEqual(
            Event.objects.count(),
            0,
        )

    def test_create_event_rejects_invalid_event_type(self):
        data = {
            "name": "Conferencia de tecnología",
            "type": 999999,
            "date": "2026-10-15T18:30:00-05:00",
            "location": "Cali",
        }

        response = self.client.post(
            "/events/",
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        response_data = response.json()

        self.assertIn(
            "type",
            response_data["errors"],
        )

        self.assertEqual(
            Event.objects.count(),
            0,
        )
    
    def test_get_events_returns_demo_user_events(self):
        event_1 = Event.objects.create(
            user=self.user,
            name="Conferencia de tecnología",
            type=self.event_type,
            date=timezone.make_aware(
                datetime(2026, 10, 15, 18, 30),
            ),
            location="Cali",
        )

        event_2 = Event.objects.create(
            user=self.user,
            name="Taller de innovación",
            type=self.event_type,
            date=timezone.make_aware(
                datetime(2026, 10, 20, 10, 0),
            ),
            location="Bogotá",
        )

        response = self.client.get(
            "/events/",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        response_data = response.json()

        self.assertTrue(
            response_data["success"],
        )

        self.assertIn(
            "data",
            response_data,
        )

        self.assertEqual(
            len(response_data["data"]),
            2,
        )

        event_ids = [
            event["id"]
            for event in response_data["data"]
        ]

        self.assertIn(
            event_1.id,
            event_ids,
        )

        self.assertIn(
            event_2.id,
            event_ids,
        )


    def test_get_events_does_not_return_events_from_other_users(self):
        other_user = User.objects.create_user(
            username="other-user",
            password="test-password",
        )

        demo_event = Event.objects.create(
            user=self.user,
            name="Evento de demo",
            type=self.event_type,
            date=timezone.make_aware(
                datetime(2026, 10, 15, 18, 30),
            ),
            location="Cali",
        )

        other_event = Event.objects.create(
            user=other_user,
            name="Evento de otro usuario",
            type=self.event_type,
            date=timezone.make_aware(
                datetime(2026, 10, 20, 10, 0),
            ),
            location="Bogotá",
        )

        response = self.client.get(
            "/events/",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        response_data = response.json()

        self.assertTrue(
            response_data["success"],
        )

        event_ids = [
            event["id"]
            for event in response_data["data"]
        ]

        self.assertIn(
            demo_event.id,
            event_ids,
        )

        self.assertNotIn(
            other_event.id,
            event_ids,
        )