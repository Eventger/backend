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

        self.assertEqual(
            response_data["message"],
            "Los datos enviados no son válidos.",
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

    def test_create_subtask_without_event_route_returns_405(self):
        response = self.client.post(
            "/subtasks/",
            {
                "name": "Subtarea sin evento",
                "target_date": "2026-10-20T08:00:00-05:00",
                "estimated_hours": "2.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 405)
        self.assertEqual(
            response.json(),
            {
                "success": False,
                "message": (
                    "El método HTTP no está permitido para este endpoint."
                ),
            },
        )
        self.assertEqual(Subtask.objects.count(), 0)

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

    def test_get_subtask_returns_subtask(self):
        subtask = Subtask.objects.create(
            event=self.event,
            name="Contratar sonido",
            target_date=timezone.now(),
            estimated_hours=Decimal("4.50"),
            details="Contactar proveedor.",
        )

        response = self.client.get(
            f"/subtasks/{subtask.id}/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
        self.assertEqual(
            response.data["data"]["id"],
            subtask.id,
        )
        self.assertEqual(
            response.data["data"]["name"],
            "Contratar sonido",
        )

    def test_get_subtask_returns_404_when_subtask_does_not_exist(self):
        response = self.client.get("/subtasks/99999/")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "success": False,
                "message": "El recurso solicitado no existe.",
            },
        )

    def test_get_subtask_returns_404_for_subtask_from_other_user(self):
        other_user = User.objects.create_user(
            username="other",
            password="test-password",
        )

        other_event = Event.objects.create(
            user=other_user,
            name="Otro evento",
            type=self.event_type,
            date=timezone.now(),
            location="Cali",
        )

        subtask = Subtask.objects.create(
            event=other_event,
            name="Subtarea protegida",
            target_date=timezone.now(),
            estimated_hours=Decimal("2.00"),
        )

        response = self.client.get(
            f"/subtasks/{subtask.id}/"
        )

        self.assertEqual(response.status_code, 404)

    def test_patch_subtask_updates_subtask(self):
        subtask = Subtask.objects.create(
            event=self.event,
            name="Nombre original",
            target_date=timezone.now(),
            estimated_hours=Decimal("2.00"),
            details="Detalles originales.",
        )

        response = self.client.patch(
            f"/subtasks/{subtask.id}/",
            {
                "name": "Nombre actualizado",
                "estimated_hours": "5.50",
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
            response.data["data"]["estimated_hours"],
            "5.50",
        )

        subtask.refresh_from_db()

        self.assertEqual(
            subtask.name,
            "Nombre actualizado",
        )
        self.assertEqual(
            subtask.estimated_hours,
            Decimal("5.50"),
        )

    def test_patch_subtask_rejects_invalid_estimated_hours(self):
        subtask = Subtask.objects.create(
            event=self.event,
            name="Subtarea",
            target_date=timezone.now(),
            estimated_hours=Decimal("2.00"),
        )

        response = self.client.patch(
            f"/subtasks/{subtask.id}/",
            {
                "estimated_hours": "0",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data["success"])
        self.assertIn(
            "estimated_hours",
            response.data["errors"],
        )

    def test_patch_subtask_updates_state(self):
        subtask = Subtask.objects.create(
            event=self.event,
            name="Subtarea pendiente",
            target_date=timezone.now(),
            estimated_hours=Decimal("2.00"),
        )

        response = self.client.patch(
            f"/subtasks/{subtask.id}/",
            {"state": Subtask.State.COMPLETED},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["data"]["state"],
            Subtask.State.COMPLETED,
        )

        subtask.refresh_from_db()
        self.assertEqual(subtask.state, Subtask.State.COMPLETED)

    def test_patch_subtask_rejects_invalid_state(self):
        subtask = Subtask.objects.create(
            event=self.event,
            name="Subtarea pendiente",
            target_date=timezone.now(),
            estimated_hours=Decimal("2.00"),
        )

        response = self.client.patch(
            f"/subtasks/{subtask.id}/",
            {"state": "invalid"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data["success"])
        self.assertIn("state", response.data["errors"])

    def test_put_subtask_updates_subtask(self):
        subtask = Subtask.objects.create(
            event=self.event,
            name="Nombre original",
            target_date=timezone.now(),
            estimated_hours=Decimal("2.00"),
            details="Detalles originales.",
        )

        new_target_date = timezone.now() + timezone.timedelta(days=3)

        response = self.client.put(
            f"/subtasks/{subtask.id}/",
            {
                "name": "Subtarea actualizada",
                "target_date": new_target_date.isoformat(),
                "estimated_hours": "6.00",
                "details": "Nuevos detalles.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
        self.assertEqual(
            response.data["data"]["name"],
            "Subtarea actualizada",
        )

        subtask.refresh_from_db()

        self.assertEqual(
            subtask.name,
            "Subtarea actualizada",
        )
        self.assertEqual(
            subtask.estimated_hours,
            Decimal("6.00"),
        )
        self.assertEqual(
            subtask.details,
            "Nuevos detalles.",
        )

    def test_delete_subtask_deletes_subtask(self):
        subtask = Subtask.objects.create(
            event=self.event,
            name="Subtarea para eliminar",
            target_date=timezone.now(),
            estimated_hours=Decimal("2.00"),
        )

        response = self.client.delete(
            f"/subtasks/{subtask.id}/"
        )

        self.assertEqual(response.status_code, 204)
        self.assertFalse(
            Subtask.objects.filter(id=subtask.id).exists()
        )
