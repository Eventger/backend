from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.events.models import Event, EventType
from apps.subtasks.models import Subtask


class EventPaginationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username="pagination-owner")
        cls.other_user = get_user_model().objects.create_user(username="pagination-other")
        event_type = EventType.objects.create(name="Conferencia")
        date = timezone.now() + timezone.timedelta(days=30)
        cls.events = [Event.objects.create(
            user=cls.user, name=f"Evento {index}", type=event_type,
            date=date, location="Cali", contact="Contacto",
        ) for index in range(13)]
        Event.objects.create(
            user=cls.other_user, name="Evento privado", type=event_type,
            date=date + timezone.timedelta(days=1), location="Cali", contact="Contacto",
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_pages_limit_downloads_and_do_not_repeat_events_with_equal_dates(self):
        received = []
        for page, expected_size in [(1, 6), (2, 6), (3, 1)]:
            with self.subTest(page=page), self.assertNumQueries(2):
                response = self.client.get("/events/", {"page": page, "page_size": 999})
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.data["success"])
            self.assertEqual(len(response.data["data"]), expected_size)
            self.assertEqual(response.data["pagination"], {
                "page": page, "page_size": 6, "total": 13, "total_pages": 3,
            })
            received.extend(event["id"] for event in response.data["data"])
        self.assertEqual(received, [event.pk for event in reversed(self.events)])

    def test_default_page_is_first(self):
        response = self.client.get("/events/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["pagination"]["page"], 1)
        self.assertEqual(len(response.data["data"]), 6)

    def test_outdated_page_uses_last_available_page_after_deletion(self):
        self.events[0].delete()
        response = self.client.get("/events/", {"page": 3})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]), 6)
        self.assertEqual(response.data["pagination"], {
            "page": 2, "page_size": 6, "total": 12, "total_pages": 2,
        })

    def test_invalid_page_is_validation_error(self):
        for page in ["abc", "0", "-1", "1.5"]:
            with self.subTest(page=page):
                response = self.client.get("/events/", {"page": page})
                self.assertEqual(response.status_code, 400)
                self.assertFalse(response.data["success"])
                self.assertIn("page", response.data["errors"])

    def test_counts_and_pages_only_include_authenticated_users_events(self):
        self.client.force_authenticate(self.other_user)
        response = self.client.get("/events/", {"page": 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["pagination"]["total"], 1)
        self.assertEqual(response.data["pagination"]["total_pages"], 1)
        self.assertEqual(response.data["data"][0]["name"], "Evento privado")

    def test_empty_account_keeps_successful_empty_list(self):
        Event.objects.filter(user=self.user).delete()
        response = self.client.get("/events/", {"page": 99})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"], [])
        self.assertEqual(response.data["pagination"], {
            "page": 1, "page_size": 6, "total": 0, "total_pages": 1,
        })

    def test_unauthenticated_request_cannot_read_events(self):
        self.assertEqual(APIClient().get("/events/").status_code, 401)

    def test_today_includes_names_for_events_outside_first_page_without_extra_queries(self):
        for event in self.events:
            Subtask.objects.create(
                event=event, name="Preparar evento", estimated_hours=1,
                target_date=timezone.now() + timezone.timedelta(days=1),
            )
        with self.assertNumQueries(4):
            response = self.client.get("/hoy/")
        self.assertEqual(response.status_code, 200)
        tasks = response.data["data"]["upcoming"]
        self.assertEqual(len(tasks), 13)
        self.assertEqual(
            {task["event"]: task["event_name"] for task in tasks},
            {event.pk: event.name for event in self.events},
        )

    def test_type_filter_is_applied_before_pagination_and_count(self):
        second_type = EventType.objects.create(name="Tipo para filtro")
        filtered_events = [Event.objects.create(
            user=self.user, name=f"Evento filtrado {index}", type=second_type,
            date=self.events[0].date - timezone.timedelta(days=1),
            location="Cali", contact="Contacto",
        ) for index in range(7)]
        Event.objects.create(
            user=self.other_user, name="Evento privado filtrado", type=second_type,
            date=self.events[0].date, location="Cali", contact="Contacto",
        )
        received = []
        for page, size in [(1, 6), (2, 1)]:
            with self.subTest(page=page), self.assertNumQueries(2):
                response = self.client.get("/events/", {"page": page, "type": second_type.pk})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.data["data"]), size)
            self.assertEqual(response.data["pagination"]["total"], 7)
            self.assertEqual(response.data["pagination"]["total_pages"], 2)
            self.assertTrue(all(item["type"] == second_type.pk for item in response.data["data"]))
            received.extend(item["id"] for item in response.data["data"])
        self.assertEqual(received, [event.pk for event in reversed(filtered_events)])

    def test_valid_type_without_matches_returns_filtered_empty_list(self):
        empty_type = EventType.objects.create(name="Tipo sin eventos propios")
        Event.objects.create(
            user=self.other_user, name="Evento ajeno", type=empty_type,
            date=self.events[0].date, location="Cali", contact="Contacto",
        )
        response = self.client.get("/events/", {"type": empty_type.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"], [])
        self.assertEqual(response.data["pagination"]["total"], 0)

    def test_invalid_type_is_validation_error(self):
        for type_id in ["abc", "0", "-1", "1.5"]:
            with self.subTest(type=type_id):
                response = self.client.get("/events/", {"type": type_id})
                self.assertEqual(response.status_code, 400)
                self.assertIn("type", response.data["errors"])

    def test_empty_optional_type_matches_unfiltered_list(self):
        response = self.client.get("/events/", {"type": ""})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["pagination"]["total"], 13)

    def test_unknown_type_returns_empty_results_and_does_not_filter_detail(self):
        response = self.client.get("/events/", {"type": 999999})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["pagination"]["total"], 0)
        response = self.client.get(f"/events/{self.events[0].pk}/", {"type": 999999})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["id"], self.events[0].pk)

    def test_search_filter_is_applied_before_pagination_and_count(self):
        event_type = self.events[0].type
        # Create events with distinctive names
        Event.objects.create(
            user=self.user, name="Gala Benéfica Anual", type=event_type,
            date=self.events[0].date, location="Cali", contact="Contacto",
        )
        Event.objects.create(
            user=self.user, name="Cena de Gala VIP", type=event_type,
            date=self.events[0].date, location="Cali", contact="Contacto",
        )
        # Search substring 'Gala'
        response = self.client.get("/events/", {"search": "gala"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["pagination"]["total"], 2)
        self.assertEqual(response.data["pagination"]["total_pages"], 1)
        names = [item["name"] for item in response.data["data"]]
        self.assertIn("Gala Benéfica Anual", names)
        self.assertIn("Cena de Gala VIP", names)

    def test_search_case_insensitive_and_substring(self):
        # "Evento 1" should match "Evento 1", "Evento 10", "Evento 11", "Evento 12"
        response = self.client.get("/events/", {"search": "evento 1"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["pagination"]["total"], 4)
        for item in response.data["data"]:
            self.assertIn("evento 1", item["name"].lower())

    def test_search_combined_with_type(self):
        second_type = EventType.objects.create(name="Tipo Exclusivo")
        matched = Event.objects.create(
            user=self.user, name="Lanzamiento de Producto Tech", type=second_type,
            date=self.events[0].date, location="Cali", contact="Contacto",
        )
        # Same name but other type
        Event.objects.create(
            user=self.user, name="Lanzamiento de Producto Moda", type=self.events[0].type,
            date=self.events[0].date, location="Cali", contact="Contacto",
        )
        response = self.client.get("/events/", {"search": "Lanzamiento", "type": second_type.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["pagination"]["total"], 1)
        self.assertEqual(response.data["data"][0]["id"], matched.pk)

    def test_search_empty_or_whitespace_is_ignored(self):
        for search_val in ["", "   "]:
            with self.subTest(search=search_val):
                response = self.client.get("/events/", {"search": search_val})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data["pagination"]["total"], 13)

    def test_search_without_matches_returns_empty_paginated_list(self):
        response = self.client.get("/events/", {"search": "Nombre Inexistente XYZ"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"], [])
        self.assertEqual(response.data["pagination"], {
            "page": 1,
            "page_size": 6,
            "total": 0,
            "total_pages": 1,
        })
