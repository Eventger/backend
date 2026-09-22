from django.contrib.auth.models import User
from django.db import models

class EventType(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True
    )
    description = models.TextField(
        blank=True
    )

    def __str__(self):
        return self.name

class Event(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events"
    )
    name = models.CharField(max_length=255)
    type = models.ForeignKey(
        EventType,
        on_delete=models.PROTECT,
        related_name="events"
    )
    date = models.DateTimeField()
    location = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name