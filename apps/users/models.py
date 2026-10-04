from django.contrib.auth.models import AbstractUser
from django.db import models
from decimal import Decimal

class User(AbstractUser):
    clerk_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
    )
    daily_limit_hours = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=Decimal("6.00"),
    )