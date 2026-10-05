from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.events.models import Event, EventType
from apps.subtasks.models import Subtask

User = get_user_model()


class SubtaskCreateViewTests(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username="task-owner",
            password="test-password",
        )
        self.client.force_authenticate(user=self.user)

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
            contact="3001234567",
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

    def test_get_subtasks_returns_404_for_event_from_other_user(self):
        other_user = User.objects.create_user(
            username="other",
            password="test-password",
        )
        other_event = Event.objects.create(
            user=other_user,
            name="Evento privado",
            type=self.event_type,
            date=timezone.now(),
            location="Bogotá",
        )

        response = self.client.get(
            f"/events/{other_event.id}/subtasks/",
        )

        self.assertEqual(response.status_code, 404)

    def test_create_subtask_returns_404_for_event_from_other_user(self):
        other_user = User.objects.create_user(
            username="other",
            password="test-password",
        )
        other_event = Event.objects.create(
            user=other_user,
            name="Evento privado",
            type=self.event_type,
            date=timezone.now(),
            location="Bogotá",
        )

        response = self.client.post(
            f"/events/{other_event.id}/subtasks/",
            {
                "name": "Tarea no autorizada",
                "target_date": timezone.now().isoformat(),
                "estimated_hours": "2.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(Subtask.objects.count(), 0)

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

    def test_patch_subtask_does_not_update_subtask_from_other_user(self):
        other_user = User.objects.create_user(
            username="other",
            password="test-password",
        )
        other_event = Event.objects.create(
            user=other_user,
            name="Evento privado",
            type=self.event_type,
            date=timezone.now(),
            location="Cali",
        )
        subtask = Subtask.objects.create(
            event=other_event,
            name="Tarea protegida",
            target_date=timezone.now(),
            estimated_hours=Decimal("2.00"),
        )

        response = self.client.patch(
            f"/subtasks/{subtask.id}/",
            {"name": "Intento de actualización"},
            format="json",
        )

        self.assertEqual(response.status_code, 404)
        subtask.refresh_from_db()
        self.assertEqual(subtask.name, "Tarea protegida")

    def test_delete_subtask_does_not_delete_subtask_from_other_user(self):
        other_user = User.objects.create_user(
            username="other",
            password="test-password",
        )
        other_event = Event.objects.create(
            user=other_user,
            name="Evento privado",
            type=self.event_type,
            date=timezone.now(),
            location="Cali",
        )
        subtask = Subtask.objects.create(
            event=other_event,
            name="Tarea protegida",
            target_date=timezone.now(),
            estimated_hours=Decimal("2.00"),
        )

        response = self.client.delete(f"/subtasks/{subtask.id}/")

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Subtask.objects.filter(id=subtask.id).exists())

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

    def test_today_returns_empty_groups(self):
        response = self.client.get("/hoy/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "success": True,
                "data": {
                    "overdue": [],
                    "today": [],
                    "upcoming": [],
                    "completed": [],
                },
            },
        )    

    def test_today_returns_overdue_subtasks(self):
        event = Event.objects.create(
            user=self.user,
            name="Evento",
            type=self.event_type,
            date=timezone.now() + timedelta(days=10),
            location="Cali",
            contact="3001234567",
        )

        subtask = Subtask.objects.create(
            event=event,
            name="Tarea vencida",
            target_date=timezone.now() - timedelta(days=1),
            estimated_hours=2,
        )

        response = self.client.get("/hoy/")

        self.assertEqual(response.status_code, 200)

        data = response.json()["data"]

        self.assertEqual(len(data["overdue"]), 1)
        self.assertEqual(data["overdue"][0]["id"], subtask.id)
        self.assertEqual(data["today"], [])
        self.assertEqual(data["upcoming"], [])
        self.assertEqual(data["completed"], [])

    def test_today_returns_today_subtasks(self):
        today_start = timezone.localtime().replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        event = Event.objects.create(
            user=self.user,
            name="Evento",
            type=self.event_type,
            date=timezone.now() + timedelta(days=10),
            location="Cali",
            contact="3001234567",
        )

        subtask = Subtask.objects.create(
            event=event,
            name="Tarea de hoy",
            target_date=today_start + timedelta(hours=10),
            estimated_hours=3,
        )

        response = self.client.get("/hoy/")

        self.assertEqual(response.status_code, 200)

        data = response.json()["data"]

        self.assertEqual(data["today"][0]["id"], subtask.id)
        self.assertEqual(data["overdue"], [])
        self.assertEqual(data["upcoming"], [])
        self.assertEqual(data["completed"], [])

    def test_today_returns_upcoming_subtasks(self):
        today_start = timezone.localtime().replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        event = Event.objects.create(
            user=self.user,
            name="Evento",
            type=self.event_type,
            date=timezone.now() + timedelta(days=10),
            location="Cali",
            contact="3001234567",
        )

        subtask = Subtask.objects.create(
            event=event,
            name="Tarea futura",
            target_date=today_start + timedelta(days=2),
            estimated_hours=4,
        )

        response = self.client.get("/hoy/")

        self.assertEqual(response.status_code, 200)

        data = response.json()["data"]

        self.assertEqual(data["upcoming"][0]["id"], subtask.id)
        self.assertEqual(data["overdue"], [])
        self.assertEqual(data["today"], [])
        self.assertEqual(data["completed"], [])

    def test_today_returns_completed_subtasks_separately(self):
        event = Event.objects.create(
            user=self.user,
            name="Evento",
            type=self.event_type,
            date=timezone.now() + timedelta(days=10),
            location="Cali",
            contact="3001234567",
        )

        subtask = Subtask.objects.create(
            event=event,
            name="Tarea completada",
            target_date=timezone.now() - timedelta(days=1),
            estimated_hours=2,
            state=Subtask.State.COMPLETED,
        )

        response = self.client.get("/hoy/")

        self.assertEqual(response.status_code, 200)

        data = response.json()["data"]

        self.assertEqual(data["completed"][0]["id"], subtask.id)
        self.assertEqual(data["overdue"], [])
        self.assertEqual(data["today"], [])
        self.assertEqual(data["upcoming"], [])

    def test_today_excludes_subtasks_from_other_users(self):
        other_user = User.objects.create_user(
            username="other",
            password="test-password",
        )

        own_event = Event.objects.create(
            user=self.user,
            name="Mi evento",
            type=self.event_type,
            date=timezone.now() + timedelta(days=10),
            location="Cali",
            contact="3001234567",
        )

        other_event = Event.objects.create(
            user=other_user,
            name="Otro evento",
            type=self.event_type,
            date=timezone.now() + timedelta(days=10),
            location="Cali",
            contact="3001234567",
        )

        own_subtask = Subtask.objects.create(
            event=own_event,
            name="Mi tarea",
            target_date=timezone.now(),
            estimated_hours=2,
        )

        Subtask.objects.create(
            event=other_event,
            name="Tarea ajena",
            target_date=timezone.now(),
            estimated_hours=1,
        )

        response = self.client.get("/hoy/")

        self.assertEqual(response.status_code, 200)

        data = response.json()["data"]

        ids = [
            subtask["id"]
            for group in data.values()
            for subtask in group
        ]

        self.assertIn(own_subtask.id, ids)
        self.assertEqual(len(ids), 1)

    def test_today_orders_subtasks_by_target_date(self):
        today_start = timezone.localtime().replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        event = Event.objects.create(
            user=self.user,
            name="Evento",
            type=self.event_type,
            date=timezone.now() + timedelta(days=10),
            location="Cali",
            contact="3001234567",
        )

        first = Subtask.objects.create(
            event=event,
            name="Primera",
            target_date=today_start + timedelta(hours=8),
            estimated_hours=1,
        )

        second = Subtask.objects.create(
            event=event,
            name="Segunda",
            target_date=today_start + timedelta(hours=12),
            estimated_hours=1,
        )

        third = Subtask.objects.create(
            event=event,
            name="Tercera",
            target_date=today_start + timedelta(hours=18),
            estimated_hours=1,
        )

        response = self.client.get("/hoy/")

        ids = [
            item["id"]
            for item in response.json()["data"]["today"]
        ]

        self.assertEqual(
            ids,
            [first.id, second.id, third.id],
        )

    def test_today_orders_same_date_by_estimated_hours(self):
        today_start = timezone.localtime().replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        event = Event.objects.create(
            user=self.user,
            name="Evento",
            type=self.event_type,
            date=timezone.now() + timedelta(days=10),
            location="Cali",
            contact="3001234567",
        )

        longer = Subtask.objects.create(
            event=event,
            name="Más horas",
            target_date=today_start + timedelta(hours=10),
            estimated_hours=5,
        )

        shorter = Subtask.objects.create(
            event=event,
            name="Menos horas",
            target_date=today_start + timedelta(hours=10),
            estimated_hours=2,
        )

        response = self.client.get("/hoy/")

        ids = [
            item["id"]
            for item in response.json()["data"]["today"]
        ]

        self.assertEqual(
            ids,
            [shorter.id, longer.id],
        )

    def test_today_includes_subtask_at_start_of_day(self):
        today_start = timezone.localtime().replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        event = Event.objects.create(
            user=self.user,
            name="Evento",
            type=self.event_type,
            date=timezone.now() + timedelta(days=10),
            location="Cali",
            contact="3001234567",
        )

        subtask = Subtask.objects.create(
            event=event,
            name="Inicio del día",
            target_date=today_start,
            estimated_hours=1,
        )

        response = self.client.get("/hoy/")

        data = response.json()["data"]

        self.assertEqual(data["today"][0]["id"], subtask.id)

    def test_today_puts_subtask_at_start_of_tomorrow_in_upcoming(self):
        today_start = timezone.localtime().replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        tomorrow_start = today_start + timedelta(days=1)

        event = Event.objects.create(
            user=self.user,
            name="Evento",
            type=self.event_type,
            date=timezone.now() + timedelta(days=10),
            location="Cali",
            contact="3001234567",
        )

        subtask = Subtask.objects.create(
            event=event,
            name="Inicio de mañana",
            target_date=tomorrow_start,
            estimated_hours=1,
        )

        response = self.client.get("/hoy/")

        data = response.json()["data"]

        self.assertEqual(data["upcoming"][0]["id"], subtask.id)

    def test_today_filters_by_status(self):
        event = Event.objects.create(
            user=self.user,
            name="Evento",
            type=self.event_type,
            date=timezone.now() + timedelta(days=10),
            location="Cali",
            contact="3001234567",
        )

        pending = Subtask.objects.create(
            event=event,
            name="Pendiente",
            target_date=timezone.now(),
            estimated_hours=1,
        )
        completed = Subtask.objects.create(
            event=event,
            name="Completada",
            target_date=timezone.now(),
            estimated_hours=1,
            state=Subtask.State.COMPLETED,
        )

        response = self.client.get(
            "/hoy/",
            {"status": Subtask.State.COMPLETED},
        )

        ids = [
            item["id"]
            for group in response.json()["data"].values()
            for item in group
        ]

        self.assertEqual(ids, [completed.id])
        self.assertNotIn(pending.id, ids)

    def test_today_filters_by_event(self):
        first_event_subtask = Subtask.objects.create(
            event=self.event,
            name="Primera tarea",
            target_date=timezone.now(),
            estimated_hours=1,
        )
        second_event = Event.objects.create(
            user=self.user,
            name="Segundo evento",
            type=self.event_type,
            date=timezone.now() + timedelta(days=10),
            location="Cali",
            contact="3001234567",
        )
        second_event_subtask = Subtask.objects.create(
            event=second_event,
            name="Segunda tarea",
            target_date=timezone.now(),
            estimated_hours=1,
        )

        response = self.client.get(
            "/hoy/",
            {"event": second_event.id},
        )

        ids = [
            item["id"]
            for group in response.json()["data"].values()
            for item in group
        ]

        self.assertEqual(ids, [second_event_subtask.id])
        self.assertNotIn(first_event_subtask.id, ids)

    def test_today_rejects_invalid_status_filter(self):
        response = self.client.get(
            "/hoy/",
            {"status": "invalid"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])

class OverloadConflictViewTests(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username="planning-owner",
            password="test-password",
            daily_limit_hours=Decimal("6.00"),
        )

        self.client.force_authenticate(
            user=self.user,
        )

        self.event_type = EventType.objects.create(
            name="Conferencia",
        )

        self.event = Event.objects.create(
            user=self.user,
            name="Conferencia de tecnología",
            type=self.event_type,
            date=timezone.make_aware(
                datetime(2026, 10, 25, 18, 30),
            ),
            location="Cali",
        )

        self.target_date = timezone.make_aware(
            datetime(2026, 10, 20, 14, 0),
        )
    def test_overload_endpoint_detects_conflict(self):
        Subtask.objects.create(
            event=self.event,
            name="Trabajo existente",
            target_date=self.target_date,
            estimated_hours=Decimal("5.00"),
        )

        subtask = Subtask.objects.create(
            event=self.event,
            name="Tarea a mover",
            target_date=self.target_date + timedelta(days=1),
            estimated_hours=Decimal("2.00"),
        )

        response = self.client.post(
            "/conflicts/overload/",
            {
                "subtask_id": subtask.id,
                "target_date": self.target_date.isoformat(),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()["data"]

        self.assertTrue(
            data["has_conflict"],
        )

        self.assertEqual(
            data["planned_hours"],
            "7.00",
        )

        self.assertEqual(
            data["limit_hours"],
            "6.00",
        )

        self.assertEqual(
            data["exceeds_by"],
            "1.00",
        )
    def test_overload_endpoint_returns_no_conflict(self):
        Subtask.objects.create(
            event=self.event,
            name="Trabajo existente",
            target_date=self.target_date,
            estimated_hours=Decimal("4.00"),
        )

        subtask = Subtask.objects.create(
            event=self.event,
            name="Tarea a mover",
            target_date=self.target_date + timedelta(days=1),
            estimated_hours=Decimal("2.00"),
        )

        response = self.client.post(
            "/conflicts/overload/",
            {
                "subtask_id": subtask.id,
                "target_date": self.target_date.isoformat(),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()["data"]

        self.assertFalse(
            data["has_conflict"],
        )

        self.assertEqual(
            data["planned_hours"],
            "6.00",
        )
    def test_overload_endpoint_returns_404_for_other_user_subtask(self):
        other_user = User.objects.create_user(
            username="other-user",
            password="test-password",
        )

        other_event = Event.objects.create(
            user=other_user,
            name="Evento privado",
            type=self.event_type,
            date=timezone.now(),
            location="Bogotá",
        )

        other_subtask = Subtask.objects.create(
            event=other_event,
            name="Subtarea ajena",
            target_date=self.target_date,
            estimated_hours=Decimal("2.00"),
        )

        response = self.client.post(
            "/conflicts/overload/",
            {
                "subtask_id": other_subtask.id,
                "target_date": self.target_date.isoformat(),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        self.assertFalse(
            response.json()["success"],
        )
    def test_overload_endpoint_does_not_modify_subtask(self):
        original_date = self.target_date + timedelta(days=1)

        subtask = Subtask.objects.create(
            event=self.event,
            name="Tarea",
            target_date=original_date,
            estimated_hours=Decimal("2.00"),
        )

        self.client.post(
            "/conflicts/overload/",
            {
                "subtask_id": subtask.id,
                "target_date": self.target_date.isoformat(),
                "estimated_hours": "1.00",
            },
            format="json",
        )

        subtask.refresh_from_db()

        self.assertEqual(
            subtask.target_date,
            original_date,
        )

        self.assertEqual(
            subtask.estimated_hours,
            Decimal("2.00"),
        )
    def test_patch_subtask_updates_target_date_when_no_conflict_exists(self):
        target_date = timezone.make_aware(
            datetime(2026, 10, 20, 14, 0),
        )

        Subtask.objects.create(
            event=self.event,
            name="Trabajo existente",
            target_date=target_date,
            estimated_hours=Decimal("4.00"),
        )

        subtask = Subtask.objects.create(
            event=self.event,
            name="Tarea a mover",
            target_date=target_date + timedelta(days=1),
            estimated_hours=Decimal("2.00"),
        )

        response = self.client.patch(
            f"/subtasks/{subtask.id}/",
            {
                "target_date": target_date.isoformat(),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        subtask.refresh_from_db()

        self.assertEqual(
            subtask.target_date,
            target_date,
        )
    def test_patch_subtask_does_not_update_when_overload_exists(self):
        target_date = timezone.make_aware(
            datetime(2026, 10, 20, 14, 0),
        )

        Subtask.objects.create(
            event=self.event,
            name="Trabajo existente",
            target_date=target_date,
            estimated_hours=Decimal("5.00"),
        )

        original_date = target_date + timedelta(days=1)

        subtask = Subtask.objects.create(
            event=self.event,
            name="Tarea a mover",
            target_date=original_date,
            estimated_hours=Decimal("2.00"),
        )

        response = self.client.patch(
            f"/subtasks/{subtask.id}/",
            {
                "target_date": target_date.isoformat(),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            409,
        )

        response_data = response.json()

        self.assertFalse(
            response_data["success"],
        )

        self.assertTrue(
            response_data["data"]["has_conflict"],
        )

        self.assertEqual(
            response_data["data"]["planned_hours"],
            "7.00",
        )

        self.assertEqual(
            response_data["data"]["limit_hours"],
            "6.00",
        )

        subtask.refresh_from_db()

        self.assertEqual(
            subtask.target_date,
            original_date,
        )
    def test_patch_subtask_resolves_conflict_by_reducing_hours(self):
        target_date = timezone.make_aware(
            datetime(2026, 10, 20, 14, 0),
        )

        Subtask.objects.create(
            event=self.event,
            name="Trabajo existente",
            target_date=target_date,
            estimated_hours=Decimal("5.00"),
        )

        subtask = Subtask.objects.create(
            event=self.event,
            name="Tarea",
            target_date=target_date + timedelta(days=1),
            estimated_hours=Decimal("2.00"),
        )

        response = self.client.patch(
            f"/subtasks/{subtask.id}/",
            {
                "target_date": target_date.isoformat(),
                "estimated_hours": "1.00",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        subtask.refresh_from_db()

        self.assertEqual(
            subtask.target_date,
            target_date,
        )

        self.assertEqual(
            subtask.estimated_hours,
            Decimal("1.00"),
        )
    def test_patch_subtask_keeps_conflict_when_reduction_is_not_enough(self):
        target_date = timezone.make_aware(
            datetime(2026, 10, 20, 14, 0),
        )

        Subtask.objects.create(
            event=self.event,
            name="Trabajo existente",
            target_date=target_date,
            estimated_hours=Decimal("5.00"),
        )

        original_date = target_date + timedelta(days=1)

        subtask = Subtask.objects.create(
            event=self.event,
            name="Tarea",
            target_date=original_date,
            estimated_hours=Decimal("3.00"),
        )

        response = self.client.patch(
            f"/subtasks/{subtask.id}/",
            {
                "target_date": target_date.isoformat(),
                "estimated_hours": "2.00",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            409,
        )

        subtask.refresh_from_db()

        self.assertEqual(
            subtask.target_date,
            original_date,
        )

        self.assertEqual(
            subtask.estimated_hours,
            Decimal("3.00"),
        )
    def test_patch_name_is_allowed_even_if_day_is_overloaded(self):
        target_date = timezone.make_aware(
            datetime(2026, 10, 20, 14, 0),
        )

        Subtask.objects.create(
            event=self.event,
            name="Otra tarea",
            target_date=target_date,
            estimated_hours=Decimal("5.00"),
        )

        subtask = Subtask.objects.create(
            event=self.event,
            name="Nombre original",
            target_date=target_date,
            estimated_hours=Decimal("2.00"),
        )

        response = self.client.patch(
            f"/subtasks/{subtask.id}/",
            {
                "name": "Nombre actualizado",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        subtask.refresh_from_db()

        self.assertEqual(
            subtask.name,
            "Nombre actualizado",
        )
    def test_patch_completed_state_is_allowed_when_day_is_overloaded(self):
        target_date = timezone.make_aware(
            datetime(2026, 10, 20, 14, 0),
        )

        Subtask.objects.create(
            event=self.event,
            name="Otra tarea",
            target_date=target_date,
            estimated_hours=Decimal("5.00"),
        )

        subtask = Subtask.objects.create(
            event=self.event,
            name="Tarea a completar",
            target_date=target_date,
            estimated_hours=Decimal("2.00"),
        )

        response = self.client.patch(
            f"/subtasks/{subtask.id}/",
            {
                "state": Subtask.State.COMPLETED,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        subtask.refresh_from_db()

        self.assertEqual(
            subtask.state,
            Subtask.State.COMPLETED,
        )
    def test_patch_completed_to_pending_is_blocked_if_it_causes_overload(self):
        target_date = timezone.make_aware(
            datetime(2026, 10, 20, 14, 0),
        )

        Subtask.objects.create(
            event=self.event,
            name="Trabajo existente",
            target_date=target_date,
            estimated_hours=Decimal("5.00"),
        )

        subtask = Subtask.objects.create(
            event=self.event,
            name="Tarea completada",
            target_date=target_date,
            estimated_hours=Decimal("2.00"),
            state=Subtask.State.COMPLETED,
        )

        response = self.client.patch(
            f"/subtasks/{subtask.id}/",
            {
                "state": Subtask.State.PENDING,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            409,
        )

        subtask.refresh_from_db()

        self.assertEqual(
            subtask.state,
            Subtask.State.COMPLETED,
        )
    def test_reprogrammed_subtask_moves_from_overdue_to_today(self):
        today_start = timezone.localtime().replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        subtask = Subtask.objects.create(
            event=self.event,
            name="Tarea vencida",
            target_date=today_start - timedelta(days=1),
            estimated_hours=Decimal("2.00"),
        )

        new_target_date = (
            today_start
            + timedelta(hours=10)
        )

        patch_response = self.client.patch(
            f"/subtasks/{subtask.id}/",
            {
                "target_date": new_target_date.isoformat(),
            },
            format="json",
        )

        self.assertEqual(
            patch_response.status_code,
            200,
        )

        response = self.client.get(
            "/hoy/",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()["data"]

        today_ids = [
            item["id"]
            for item in data["today"]
        ]

        overdue_ids = [
            item["id"]
            for item in data["overdue"]
        ]

        self.assertIn(
            subtask.id,
            today_ids,
        )

        self.assertNotIn(
            subtask.id,
            overdue_ids,
        )