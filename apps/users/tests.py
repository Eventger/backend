from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase


User = get_user_model()


class UserModelTests(TestCase):

    def test_daily_limit_hours_defaults_to_six(self):
        user = User.objects.create_user(
            username="test-user",
            password="test-password",
        )

        self.assertEqual(
            user.daily_limit_hours,
            Decimal("6.00"),
        )

    def test_daily_limit_hours_can_be_changed(self):
        user = User.objects.create_user(
            username="test-user",
            password="test-password",
            daily_limit_hours=Decimal("8.00"),
        )

        self.assertEqual(
            user.daily_limit_hours,
            Decimal("8.00"),
        )

    def test_email_is_trimmed_and_password_is_preserved_exactly(self):
        user = User.objects.create_user(
            username="test-trim-user",
            password="  raw-password-with-spaces  ",
            email="  user@example.com  ",
        )

        self.assertEqual(user.email, "user@example.com")
        self.assertTrue(user.check_password("  raw-password-with-spaces  "))
        self.assertFalse(user.check_password("raw-password-with-spaces"))