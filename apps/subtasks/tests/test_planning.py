from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from threading import Barrier
from unittest.mock import patch as mock_patch

from django.contrib.auth import get_user_model
from django.db import connections
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.events.models import Event, EventType
from apps.subtasks.models import Subtask

User = get_user_model()


class PlanningFixture:
    def setUp(self):
        self.user = User.objects.create_user(username="planning-owner")
        self.other = User.objects.create_user(username="planning-other")
        self.type = EventType.objects.create(name="Boda")
        self.day = timezone.localdate() + timedelta(days=3)
        self.event = Event.objects.create(
            user=self.user, name="Evento", type=self.type,
            date=self.at(self.day + timedelta(days=15)), location="Cali", contact="Cliente",
        )
        self.task = self.create_task("Buscar proveedores", self.day - timedelta(days=1), 2)
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def at(self, day):
        return timezone.make_aware(datetime.combine(day, datetime.min.time()))

    def create_task(self, name, day, hours, event=None, state="pending"):
        return Subtask.objects.create(
            event=event or self.event, name=name, target_date=self.at(day),
            estimated_hours=Decimal(str(hours)), state=state,
        )

    def preview(self, **changes):
        return self.client.post(f"/subtasks/{self.task.pk}/reschedule-preview/", {
            "target_date": self.day.isoformat(), **changes,
        }, format="json")

    def patch(self, **changes):
        return self.client.patch(f"/subtasks/{self.task.pk}/", {
            "target_date": self.at(self.day).isoformat(), **changes,
        }, format="json")


class PlanningTests(PlanningFixture, TestCase):
    def test_preview_and_writes_reject_past_dates_without_mutating_task(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        self.assertEqual(self.preview(target_date=yesterday.isoformat()).status_code, 400)
        original = (self.task.target_date, self.task.name, self.task.estimated_hours)
        for method in [self.client.patch, self.client.put]:
            response = method(f"/subtasks/{self.task.pk}/", {
                "target_date": self.at(yesterday).isoformat(), "name": "No guardar",
                "estimated_hours": "1.00", "state": "pending",
            }, format="json")
            self.assertEqual(response.status_code, 400)
            self.assertIn("target_date", response.data["errors"])
            self.task.refresh_from_db()
            self.assertEqual((self.task.target_date, self.task.name, self.task.estimated_hours), original)

    def test_today_is_allowed_using_the_bogota_calendar_at_utc_midnight(self):
        today = timezone.localdate()
        now = datetime.combine(today + timedelta(days=1), datetime.min.time()).replace(hour=2, tzinfo=UTC)
        with mock_patch("django.utils.timezone.now", return_value=now):
            self.assertEqual(self.preview(target_date=today.isoformat()).status_code, 200)
            target = f"{(today + timedelta(days=1)).isoformat()}T02:00:00Z"
            self.assertEqual(self.patch(target_date=target).status_code, 200)
            yesterday = f"{today.isoformat()}T02:00:00Z"
            self.assertEqual(self.patch(target_date=yesterday).status_code, 400)

    def test_existing_overdue_tasks_can_still_be_edited_without_moving_to_the_past(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        self.task.target_date = self.at(yesterday)
        self.task.save()
        response = self.client.patch(f"/subtasks/{self.task.pk}/", {
            "target_date": self.task.target_date.isoformat(), "details": "Nota actualizada",
            "estimated_hours": "1.00", "state": "completed",
        }, format="json")
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(timezone.localdate(self.task.target_date), yesterday)
        self.assertEqual(self.task.details, "Nota actualizada")
        self.assertEqual(self.task.state, "completed")

    def test_default_and_preferences_persist_independently(self):
        url = "/api/auth/preferences/"
        self.assertEqual(self.client.get(url).data["data"]["daily_limit_hours"], "6.00")
        self.assertEqual(self.client.put(url, {"daily_limit_hours": "4.50"}, format="json").status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.daily_limit_hours, Decimal("4.50"))
        self.assertTrue(self.user.daily_limit_configured)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(url).data["data"]["daily_limit_hours"], "6.00")

    def test_limit_range_and_precision(self):
        for value in ["0.50", "0", "16.01", "24", "1.001", "NaN"]:
            with self.subTest(value=value):
                self.assertEqual(self.client.put("/api/auth/preferences/", {"daily_limit_hours": value}, format="json").status_code, 400)
        for value in ["1", "16"]:
            self.assertEqual(self.client.put("/api/auth/preferences/", {"daily_limit_hours": value}, format="json").status_code, 200)

    def test_legacy_import_cannot_overwrite_a_configured_limit(self):
        self.client.put("/api/auth/preferences/", {"daily_limit_hours": "4"}, format="json")
        result = self.client.put("/api/auth/preferences/", {"daily_limit_hours": "8", "only_if_unconfigured": True}, format="json")
        self.assertEqual(result.data["data"]["daily_limit_hours"], "4.00")

    def test_conflict_preview_is_read_only_and_patch_does_not_persist(self):
        self.create_task("Catering", self.day, 5)
        preview = self.preview()
        self.assertEqual(preview.status_code, 200)
        self.assertEqual(Decimal(preview.data["data"]["planned_hours"]), 7)
        self.assertTrue(preview.data["data"]["has_conflict"])
        before = self.task.target_date
        self.assertEqual(self.patch().status_code, 409)
        self.task.refresh_from_db()
        self.assertEqual(self.task.target_date, before)

    def test_equal_to_limit_is_allowed_and_appears_in_today(self):
        self.create_task("Catering", self.day, 4)
        self.assertFalse(self.preview().data["data"]["has_conflict"])
        self.assertEqual(self.patch().status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(timezone.localdate(self.task.target_date), self.day)
        ids = [item["id"] for item in self.client.get("/hoy/").data["data"]["upcoming"]]
        self.assertIn(self.task.pk, ids)

    def test_counts_all_events_excludes_completed_other_organizers_and_self(self):
        another = Event.objects.create(user=self.user, name="Otro", type=self.type, date=self.event.date, location="Cali", contact="Cliente")
        foreign = Event.objects.create(user=self.other, name="Privado", type=self.type, date=self.event.date, location="Cali", contact="Cliente")
        self.create_task("Otro evento", self.day, 5, event=another)
        self.create_task("Ya ejecutada", self.day, 12, state="completed")
        self.create_task("Privada", self.day, 12, event=foreign)
        self.task.target_date = self.at(self.day)
        self.task.save()
        plan = self.preview().data["data"]
        self.assertEqual(Decimal(plan["planned_hours"]), 7)
        self.assertEqual([item["name"] for item in plan["tasks"]], ["Otro evento"])

    def test_resolution_by_suggestion_and_reducing_hours(self):
        self.create_task("Catering", self.day, 5)
        suggested = self.preview().data["data"]["suggestion"]["date"]
        result = self.patch(target_date=self.at(datetime.fromisoformat(suggested).date()).isoformat())
        self.assertEqual(result.status_code, 200)
        self.assertEqual(self.patch(estimated_hours="1.50").status_code, 409)
        self.assertEqual(self.patch(estimated_hours="1.00").status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.estimated_hours, Decimal("1.00"))

    def test_preview_and_preferences_require_authentication_and_ownership(self):
        self.client.force_authenticate(self.other)
        self.assertEqual(self.preview().status_code, 404)
        self.client = APIClient()
        self.assertEqual(self.preview().status_code, 401)
        self.assertEqual(self.client.get("/api/auth/preferences/").status_code, 401)

    def test_preview_rejects_invalid_date_hours_and_after_event(self):
        for data in [{"target_date": "invalid"}, {"estimated_hours": "0"}, {"target_date": (self.day + timedelta(days=16)).isoformat()}]:
            self.assertEqual(self.preview(**data).status_code, 400)

    def test_preview_stale_after_capacity_changes_is_rechecked_at_save(self):
        self.create_task("Catering", self.day, 4)
        self.assertFalse(self.preview().data["data"]["has_conflict"])
        self.client.put("/api/auth/preferences/", {"daily_limit_hours": "4"}, format="json")
        self.assertEqual(self.patch().status_code, 409)

    def test_bogota_calendar_and_no_viable_suggestion(self):
        # 02:00 UTC pertenece al día anterior en Bogotá.
        morning_task = self.create_task("Madrugada", self.day, 5)
        Subtask.objects.filter(pk=morning_task.pk).update(
            target_date=f"{(self.day + timedelta(days=1)).isoformat()}T02:00:00Z",
        )
        self.assertEqual(Decimal(self.preview().data["data"]["existing_hours"]), 5)
        self.assertIsNone(self.preview(estimated_hours="7").data["data"]["suggestion"])

    def test_non_planning_edits_and_completed_tasks_are_preserved(self):
        self.create_task("Catering", self.day - timedelta(days=1), 12)
        response = self.client.patch(f"/subtasks/{self.task.pk}/", {"details": "Nueva nota"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.patch(state="completed").status_code, 200)


class PlanningConcurrencyTests(PlanningFixture, TransactionTestCase):
    def test_two_reprogramming_requests_cannot_both_overload_the_day(self):
        self.task.estimated_hours = Decimal("3")
        self.task.save()
        second = self.create_task("Decoración", self.day - timedelta(days=2), 3)
        self.create_task("Carga existente", self.day, 2)
        barrier = Barrier(2)

        def reprogram(task_id):
            try:
                client = APIClient()
                client.force_authenticate(User.objects.get(pk=self.user.pk))
                barrier.wait(timeout=10)
                return client.patch(f"/subtasks/{task_id}/", {"target_date": self.at(self.day).isoformat()}, format="json").status_code
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(reprogram, [self.task.pk, second.pk]))
        self.assertEqual(sorted(results), [200, 409])


class PlanningDeadlineTests(PlanningFixture, TestCase):
    def test_patch_and_put_reject_after_event_without_changing_other_fields(self):
        original = (self.task.name, self.task.target_date, self.task.estimated_hours)
        for method in [self.client.patch, self.client.put]:
            response = method(f"/subtasks/{self.task.pk}/", {
                "name": "No debe guardarse", "target_date": self.at(self.day + timedelta(days=16)).isoformat(),
                "estimated_hours": "3.00", "state": "completed",
            }, format="json")
            self.assertEqual(response.status_code, 400)
            self.assertIn("target_date", response.data["errors"])
            self.task.refresh_from_db()
            self.assertEqual((self.task.name, self.task.target_date, self.task.estimated_hours), original)
            self.assertEqual(self.task.state, "pending")

    def test_event_patch_and_put_reject_deadline_before_tasks(self):
        original = (self.event.name, self.event.date)
        for method in [self.client.patch, self.client.put]:
            response = method(f"/events/{self.event.pk}/", {
                "name": "No debe guardarse", "type": self.type.pk,
                "date": self.at(self.day - timedelta(days=2)).isoformat(),
                "location": "Cali", "contact": "Cliente",
            }, format="json")
            self.assertEqual(response.status_code, 400)
            self.assertIn(self.task.name, str(response.data["errors"]["date"]))
            self.event.refresh_from_db()
            self.assertEqual((self.event.name, self.event.date), original)

    def test_event_can_move_to_same_bogota_day_as_latest_task(self):
        date = timezone.localdate(self.task.target_date)
        response = self.client.patch(f"/events/{self.event.pk}/", {"date": self.at(date).isoformat()}, format="json")
        self.assertEqual(response.status_code, 200)
        # UTC del día siguiente sigue siendo el mismo día en Bogotá.
        target = f"{(date + timedelta(days=1)).isoformat()}T02:00:00Z"
        self.assertEqual(self.client.patch(f"/subtasks/{self.task.pk}/", {"target_date": target}, format="json").status_code, 200)

    def test_event_change_invalidates_previous_preview_at_save(self):
        target = self.day + timedelta(days=1)
        self.assertEqual(self.preview(target_date=target.isoformat()).status_code, 200)
        self.assertEqual(self.client.patch(f"/events/{self.event.pk}/", {"date": self.at(self.day).isoformat()}, format="json").status_code, 200)
        self.assertEqual(self.patch(target_date=self.at(target).isoformat()).status_code, 400)
        self.task.refresh_from_db()
        self.assertEqual(timezone.localdate(self.task.target_date), self.day - timedelta(days=1))

    def test_existing_invalid_task_can_still_be_completed_or_annotated(self):
        Subtask.objects.filter(pk=self.task.pk).update(target_date=self.at(self.day + timedelta(days=16)))
        response = self.client.patch(f"/subtasks/{self.task.pk}/", {"details": "Conservar avance", "state": "completed"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.details, "Conservar avance")
        self.assertEqual(self.task.state, "completed")


class PlanningDeadlineConcurrencyTests(PlanningFixture, TransactionTestCase):
    def test_event_and_task_updates_cannot_leave_task_after_event(self):
        barrier = Barrier(2)

        def write(kind):
            try:
                client = APIClient()
                client.force_authenticate(User.objects.get(pk=self.user.pk))
                barrier.wait(timeout=10)
                if kind == "event":
                    return client.patch(f"/events/{self.event.pk}/", {"date": self.at(self.day).isoformat()}, format="json").status_code
                return client.patch(f"/subtasks/{self.task.pk}/", {"target_date": self.at(self.day + timedelta(days=1)).isoformat()}, format="json").status_code
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(write, ["event", "task"]))
        self.assertEqual(sorted(results), [200, 400])
        self.event.refresh_from_db()
        self.task.refresh_from_db()
        self.assertLessEqual(timezone.localdate(self.task.target_date), timezone.localdate(self.event.date))
