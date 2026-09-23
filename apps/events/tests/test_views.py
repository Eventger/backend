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

    def test_get_event_returns_event(self):
        event = Event.objects.create(
            user=self.user,
            name="Conferencia",
            type=self.event_type,
            date=timezone.now(),
            location="Bogotá",
        )

        response = self.client.get(f"/events/{event.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["id"], event.id)
        self.assertEqual(response.data["data"]["name"], "Conferencia")

    def test_get_event_returns_404_when_event_does_not_exist(self):
        response = self.client.get("/events/99999/")

        self.assertEqual(response.status_code, 404)

    def test_get_event_returns_404_for_event_from_other_user(self):
        other_user = User.objects.create_user(
            username="other",
            password="test-password",
        )

        event = Event.objects.create(
            user=other_user,
            name="Evento privado",
            type=self.event_type,
            date=timezone.now(),
            location="Cali",
        )

        response = self.client.get(f"/events/{event.id}/")

        self.assertEqual(response.status_code, 404)

    def test_patch_event_updates_event(self):
        event = Event.objects.create(
            user=self.user,
            name="Nombre original",
            type=self.event_type,
            date=timezone.now(),
            location="Bogotá",
        )

        response = self.client.patch(
            f"/events/{event.id}/",
            {
                "name": "Nombre actualizado",
                "location": "Cali",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
        self.assertEqual(
            response.data["data"]["name"],
            "Nombre actualizado",
        )
        self.assertEqual(
            response.data["data"]["location"],
            "Cali",
        )

        event.refresh_from_db()

        self.assertEqual(event.name, "Nombre actualizado")
        self.assertEqual(event.location, "Cali")

    def test_patch_event_rejects_blank_name(self):
        event = Event.objects.create(
            user=self.user,
            name="Evento original",
            type=self.event_type,
            date=timezone.now(),
            location="Bogotá",
        )

        response = self.client.patch(
            f"/events/{event.id}/",
            {
                "name": "   ",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data["success"])
        self.assertIn("name", response.data["errors"])

    def test_put_event_updates_event(self):
        event = Event.objects.create(
            user=self.user,
            name="Evento original",
            type=self.event_type,
            date=timezone.now(),
            location="Bogotá",
        )

        new_date = timezone.now() + timezone.timedelta(days=5)

        response = self.client.put(
            f"/events/{event.id}/",
            {
                "name": "Evento actualizado",
                "type": self.event_type.id,
                "date": new_date.isoformat(),
                "location": "Medellín",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
        self.assertEqual(
            response.data["data"]["name"],
            "Evento actualizado",
        )

        event.refresh_from_db()

        self.assertEqual(event.name, "Evento actualizado")
        self.assertEqual(event.location, "Medellín")

    def test_delete_event_deletes_event(self):
        event = Event.objects.create(
            user=self.user,
            name="Evento para eliminar",
            type=self.event_type,
            date=timezone.now(),
            location="Bogotá",
        )

        response = self.client.delete(
            f"/events/{event.id}/",
        )

        self.assertEqual(response.status_code, 204)
        self.assertFalse(
            Event.objects.filter(id=event.id).exists()
        )

    def test_delete_event_does_not_delete_event_from_other_user(self):
        other_user = User.objects.create_user(
            username="other",
            password="test-password",
        )

        event = Event.objects.create(
            user=other_user,
            name="Evento protegido",
            type=self.event_type,
            date=timezone.now(),
            location="Cali",
        )

        response = self.client.delete(
            f"/events/{event.id}/",
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(
            Event.objects.filter(id=event.id).exists()
        )