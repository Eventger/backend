from django.test import TestCase

from apps.events.models import EventType
from apps.events.serializers import EventSerializer
from django.utils import timezone
from datetime import timedelta

class EventSerializerTests(TestCase):

    def setUp(self):
        self.event_type = EventType.objects.create(
            name="Conferencia",
        )

        self.data = {
            "name": "Conferencia de tecnología",
            "type": self.event_type.id,
            "date": (timezone.now() + timedelta(days=1)).isoformat(),
            "location": "Cali",
            "contact": "Juan Pérez",
        }

    def test_valid_event_data(self):
        data = {
            "name": "Conferencia de tecnología",
            "type": self.event_type.id,
            "date": "2026-10-15T18:30:00-05:00",
            "location": "Cali",
            "contact": "Juan Pérez",
        }

        serializer = EventSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data["name"],
            "Conferencia de tecnología",
        )
        self.assertEqual(
            serializer.validated_data["location"],
            "Cali",
        )

    def test_required_fields(self):
        serializer = EventSerializer(data={})

        self.assertFalse(serializer.is_valid())

        self.assertIn("name", serializer.errors)
        self.assertIn("type", serializer.errors)
        self.assertIn("date", serializer.errors)
        self.assertIn("location", serializer.errors)

    def test_name_cannot_be_only_whitespace(self):
        data = {
            "name": "   ",
            "type": self.event_type.id,
            "date": "2026-10-15T18:30:00-05:00",
            "location": "Cali",
        }

        serializer = EventSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)

    def test_location_cannot_be_only_whitespace(self):
        data = {
            "name": "Conferencia de tecnología",
            "type": self.event_type.id,
            "date": "2026-10-15T18:30:00-05:00",
            "location": "   ",
        }

        serializer = EventSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("location", serializer.errors)

    def test_invalid_event_type(self):
        data = {
            "name": "Conferencia de tecnología",
            "type": 999999,
            "date": "2026-10-15T18:30:00-05:00",
            "location": "Cali",
        }

        serializer = EventSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("type", serializer.errors)

    def test_contact_is_valid(self):
        data = self.data.copy()
        data["contact"] = "Juan Pérez"

        serializer = EventSerializer(data=data)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["contact"], "Juan Pérez")

    def test_contact_is_stripped(self):
        data = self.data.copy()
        data["contact"] = "   Juan Pérez   "

        serializer = EventSerializer(data=data)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["contact"], "Juan Pérez")

    def test_contact_cannot_be_blank(self):
        data = self.data.copy()
        data["contact"] = ""

        serializer = EventSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("contact", serializer.errors)

    def test_contact_cannot_contain_only_spaces(self):
        data = self.data.copy()
        data["contact"] = "     "

        serializer = EventSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("contact", serializer.errors)

    def test_contact_is_required(self):
        data = self.data.copy()
        data.pop("contact", None)

        serializer = EventSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("contact", serializer.errors)

    def test_event_date_must_be_future(self):
        data = self.data.copy()
        data["date"] = timezone.now() + timedelta(days=1)

        serializer = EventSerializer(data=data)

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_event_date_cannot_be_in_the_past(self):
        data = self.data.copy()
        data["date"] = timezone.now() - timedelta(days=1)

        serializer = EventSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("date", serializer.errors)

    def test_event_date_cannot_be_now(self):
        current_time = timezone.now()

        data = self.data.copy()
        data["date"] = current_time

        serializer = EventSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("date", serializer.errors)

    def test_text_fields_accept_exactly_255_characters(self):
        for field in ("name", "location", "contact"):
            with self.subTest(field=field):
                data = self.data.copy()
                data[field] = "a" * 255

                serializer = EventSerializer(data=data)

                self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_text_fields_reject_more_than_255_characters(self):
        for field in ("name", "location", "contact"):
            with self.subTest(field=field):
                data = self.data.copy()
                data[field] = "a" * 256

                serializer = EventSerializer(data=data)

                self.assertFalse(serializer.is_valid())
                self.assertIn(field, serializer.errors)

    def test_event_date_rejects_invalid_format(self):
        data = self.data.copy()
        data["date"] = "fecha-invalida"

        serializer = EventSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("date", serializer.errors)
