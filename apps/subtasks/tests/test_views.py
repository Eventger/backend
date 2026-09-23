from datetime import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.events.models import Event, EventType
from apps.subtasks.models import Subtask


class SubtaskCreateViewTests(TestCase):

    def setUp(self):
        self.client = APIClient()

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

    def test_create_subtask_returns_201(self):
        data = {
            "name": "Confirmar proveedor de sonido",
            "target_date": "2026-10-20T14:00:00-05:00",
            "estimated_hours": "2.50",
            "details": "Contactar al proveedor.",
        }

        response = self.client.post(
            f"/events/{self.event.id}/subtasks/",
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        response_data = response.json()

        self.assertTrue(
            response_data["success"],
        )

        self.assertEqual(
            response_data["message"],
            "Subtarea creada correctamente.",
        )

        self.assertIn(
            "data",
            response_data,
        )

        subtask_data = response_data["data"]

        self.assertEqual(
            subtask_data["name"],
            "Confirmar proveedor de sonido",
        )

        self.assertEqual(
            subtask_data["event"],
            self.event.id,
        )

        self.assertEqual(
            subtask_data["state"],
            "pending",
        )

        self.assertTrue(
            Subtask.objects.filter(
                event=self.event,
                name="Confirmar proveedor de sonido",
            ).exists()
        )

    def test_create_subtask_returns_400_when_required_fields_are_missing(
        self,
    ):
        response = self.client.post(
            f"/events/{self.event.id}/subtasks/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        response_data = response.json()

        self.assertFalse(
            response_data["success"],
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
            "target_date",
            response_data["errors"],
        )

        self.assertIn(
            "estimated_hours",
            response_data["errors"],
        )

        self.assertEqual(
            Subtask.objects.count(),
            0,
        )

    def test_create_subtask_rejects_blank_name(self):
        data = {
            "name": "   ",
            "target_date": "2026-10-20T14:00:00-05:00",
            "estimated_hours": "2.50",
        }

        response = self.client.post(
            f"/events/{self.event.id}/subtasks/",
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
            Subtask.objects.count(),
            0,
        )

    def test_create_subtask_rejects_zero_estimated_hours(self):
        data = {
            "name": "Montar escenario",
            "target_date": "2026-10-20T08:00:00-05:00",
            "estimated_hours": "0",
        }

        response = self.client.post(
            f"/events/{self.event.id}/subtasks/",
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        response_data = response.json()

        self.assertIn(
            "estimated_hours",
            response_data["errors"],
        )

        self.assertEqual(
            Subtask.objects.count(),
            0,
        )

    def test_create_subtask_rejects_negative_estimated_hours(self):
        data = {
            "name": "Montar escenario",
            "target_date": "2026-10-20T08:00:00-05:00",
            "estimated_hours": "-2",
        }

        response = self.client.post(
            f"/events/{self.event.id}/subtasks/",
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        response_data = response.json()

        self.assertIn(
            "estimated_hours",
            response_data["errors"],
        )

        self.assertEqual(
            Subtask.objects.count(),
            0,
        )

    def test_create_subtask_returns_404_when_event_does_not_exist(self):
        response = self.client.post(
            "/events/999999/subtasks/",
            {
                "name": "Subtarea de prueba",
                "target_date": "2026-10-20T08:00:00-05:00",
                "estimated_hours": "2",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        response_data = response.json()

        self.assertFalse(
            response_data["success"],
        )

        self.assertEqual(
            response_data["message"],
            "El evento no existe.",
        )

        self.assertEqual(
            Subtask.objects.count(),
            0,
        )

    def test_get_subtasks_returns_event_subtasks(self):
        subtask_1 = Subtask.objects.create(
            event=self.event,
            name="Confirmar proveedor de sonido",
            target_date=timezone.make_aware(
                datetime(2026, 10, 20, 14, 0),
            ),
            estimated_hours=Decimal("2.50"),
            details="Contactar al proveedor.",
        )

        subtask_2 = Subtask.objects.create(
            event=self.event,
            name="Reservar lugar",
            target_date=timezone.make_aware(
                datetime(2026, 10, 21, 10, 0),
            ),
            estimated_hours=Decimal("3.00"),
        )

        response = self.client.get(
            f"/events/{self.event.id}/subtasks/",
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

        subtask_ids = [
            subtask["id"]
            for subtask in response_data["data"]
        ]

        self.assertIn(
            subtask_1.id,
            subtask_ids,
        )

        self.assertIn(
            subtask_2.id,
            subtask_ids,
        )

    def test_get_subtasks_does_not_return_subtasks_from_other_events(self):
        other_event = Event.objects.create(
            user=self.user,
            name="Otro evento",
            type=self.event_type,
            date=timezone.make_aware(
                datetime(2026, 11, 15, 18, 30),
            ),
            location="Bogotá",
        )

        event_subtask = Subtask.objects.create(
            event=self.event,
            name="Subtarea del evento principal",
            target_date=timezone.make_aware(
                datetime(2026, 10, 20, 14, 0),
            ),
            estimated_hours=Decimal("2.00"),
        )

        other_subtask = Subtask.objects.create(
            event=other_event,
            name="Subtarea de otro evento",
            target_date=timezone.make_aware(
                datetime(2026, 11, 20, 14, 0),
            ),
            estimated_hours=Decimal("4.00"),
        )

        response = self.client.get(
            f"/events/{self.event.id}/subtasks/",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        response_data = response.json()

        self.assertTrue(
            response_data["success"],
        )

        subtask_ids = [
            subtask["id"]
            for subtask in response_data["data"]
        ]

        self.assertIn(
            event_subtask.id,
            subtask_ids,
        )

        self.assertNotIn(
            other_subtask.id,
            subtask_ids,
        )

    def test_get_subtasks_returns_404_when_event_does_not_exist(self):
        response = self.client.get(
            "/events/999999/subtasks/",
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        response_data = response.json()

        self.assertFalse(
            response_data["success"],
        )

        self.assertEqual(
            response_data["message"],
            "El evento no existe.",
        )

    def test_get_subtasks_returns_empty_list_when_event_has_no_subtasks(self):
        response = self.client.get(
            f"/events/{self.event.id}/subtasks/",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        response_data = response.json()

        self.assertTrue(
            response_data["success"],
        )

        self.assertEqual(
            response_data["data"],
            [],
        )