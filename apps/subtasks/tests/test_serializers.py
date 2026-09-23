from decimal import Decimal
from django.test import TestCase

from apps.subtasks.serializers import SubtaskSerializer


class SubtaskSerializerTests(TestCase):

    def test_valid_subtask_data(self):
        data = {
            "name": "Confirmar proveedor de sonido",
            "target_date": "2026-10-20T14:00:00-05:00",
            "estimated_hours": "2.50",
            "details": "Contactar al proveedor.",
        }

        serializer = SubtaskSerializer(data=data)

        self.assertTrue(
            serializer.is_valid(),
        )

        self.assertEqual(
            serializer.validated_data["name"],
            "Confirmar proveedor de sonido",
        )

        self.assertEqual(
            serializer.validated_data["estimated_hours"],
            Decimal("2.50"),
        )

    def test_required_fields(self):
        serializer = SubtaskSerializer(data={})

        self.assertFalse(
            serializer.is_valid(),
        )

        self.assertIn(
            "name",
            serializer.errors,
        )

        self.assertIn(
            "target_date",
            serializer.errors,
        )

        self.assertIn(
            "estimated_hours",
            serializer.errors,
        )

    def test_name_cannot_be_only_whitespace(self):
        data = {
            "name": "   ",
            "target_date": "2026-10-20T14:00:00-05:00",
            "estimated_hours": "2.50",
        }

        serializer = SubtaskSerializer(data=data)

        self.assertFalse(
            serializer.is_valid(),
        )

        self.assertIn(
            "name",
            serializer.errors,
        )

    def test_estimated_hours_must_be_greater_than_zero(self):
        data = {
            "name": "Montar escenario",
            "target_date": "2026-10-20T14:00:00-05:00",
            "estimated_hours": "0",
        }

        serializer = SubtaskSerializer(data=data)

        self.assertFalse(
            serializer.is_valid(),
        )

        self.assertIn(
            "estimated_hours",
            serializer.errors,
        )

    def test_estimated_hours_cannot_be_negative(self):
        data = {
            "name": "Montar escenario",
            "target_date": "2026-10-20T14:00:00-05:00",
            "estimated_hours": "-2",
        }

        serializer = SubtaskSerializer(data=data)

        self.assertFalse(
            serializer.is_valid(),
        )

        self.assertIn(
            "estimated_hours",
            serializer.errors,
        )

    def test_state_is_read_only(self):
        data = {
            "name": "Montar escenario",
            "target_date": "2026-10-20T08:00:00-05:00",
            "estimated_hours": "2.50",
            "state": "completed",
        }

        serializer = SubtaskSerializer(data=data)

        self.assertTrue(
            serializer.is_valid(),
        )

        self.assertNotIn(
            "state",
            serializer.validated_data,
        )