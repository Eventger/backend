from django.contrib.auth.models import AbstractUser
from django.db import models
from decimal import Decimal
from django.core.validators import MaxValueValidator, MinValueValidator


class User(AbstractUser):
    daily_limit_hours = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=Decimal("6.00"),
        validators=[MinValueValidator(1), MaxValueValidator(16)],
    )
    daily_limit_configured = models.BooleanField(default=False)

    class Meta(AbstractUser.Meta):
        abstract = False
        constraints = [
            models.CheckConstraint(
                condition=models.Q(daily_limit_hours__gte=1, daily_limit_hours__lte=16),
                name="user_daily_limit_between_1_and_16",
            ),
        ]

    clerk_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
    )

    def clean(self):
        super().clean()
        if self.email:
            self.email = self.email.strip()

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.strip()
        super().save(*args, **kwargs)
