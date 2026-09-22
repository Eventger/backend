from django.test import TestCase

from apps.events.models import EventType
from apps.events.serializers import EventSerializer


class EventSerializerTests(TestCase):

    def test_valid_event_data(self):
        event_type = EventType.objects.create(
            name="Conferencia",
        )

        data = {
            "name": "Conferencia de tecnología",
            "type": event_type.id,
            "date": "2026-10-15T18:30:00-05:00",
            "location": "Cali",
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
        event_type = EventType.objects.create(
            name="Conferencia",
        )

        data = {
            "name": "   ",
            "type": event_type.id,
            "date": "2026-10-15T18:30:00-05:00",
            "location": "Cali",
        }

        serializer = EventSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)

    def test_location_cannot_be_only_whitespace(self):
        event_type = EventType.objects.create(
            name="Conferencia",
        )

        data = {
            "name": "Conferencia de tecnología",
            "type": event_type.id,
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