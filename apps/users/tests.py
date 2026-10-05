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