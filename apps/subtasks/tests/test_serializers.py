from decimal import Decimal
from django.test import TestCase

from apps.subtasks.serializers import SubtaskSerializer


class SubtaskSerializerTests(TestCase):

    def setUp(self):
        self.data = {
            "name": "Confirmar proveedor de sonido",
            "target_date": "2026-10-20T14:00:00-05:00",
            "estimated_hours": "2.50",
            "details": "Contactar al proveedor.",
        }

    def test_valid_subtask_data(self):
        serializer = SubtaskSerializer(data=self.data)

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

    def test_name_accepts_exactly_255_characters(self):
        data = self.data.copy()
        data["name"] = "a" * 255

        serializer = SubtaskSerializer(data=data)

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_name_rejects_more_than_255_characters(self):
        data = self.data.copy()
        data["name"] = "a" * 256

        serializer = SubtaskSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)

    def test_estimated_hours_accepts_decimal_field_limits(self):
        for value in ("0.01", "99999999.99"):
            with self.subTest(value=value):
                data = self.data.copy()
                data["estimated_hours"] = value

                serializer = SubtaskSerializer(data=data)

                self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_estimated_hours_rejects_too_many_digits(self):
        data = self.data.copy()
        data["estimated_hours"] = "100000000.00"

        serializer = SubtaskSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("estimated_hours", serializer.errors)

    def test_estimated_hours_rejects_too_many_decimal_places(self):
        data = self.data.copy()
        data["estimated_hours"] = "1.999"

        serializer = SubtaskSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("estimated_hours", serializer.errors)

    def test_estimated_hours_rejects_non_numeric_value(self):
        data = self.data.copy()
        data["estimated_hours"] = "dos horas"

        serializer = SubtaskSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("estimated_hours", serializer.errors)

    def test_target_date_rejects_invalid_format(self):
        data = self.data.copy()
        data["target_date"] = "fecha-invalida"

        serializer = SubtaskSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("target_date", serializer.errors)
