from datetime import datetime

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