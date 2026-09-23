from django.db import models
from apps.events.models import Event

class Subtask(models.Model):
    class State(models.TextChoices):
        PENDING = "pending", "Pendiente"
        IN_PROGRESS = "in_progress", "En Progreso"
        COMPLETED = "completed", "Completada"

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="subtasks"
    )
    name = models.CharField(max_length=255)
    target_date = models.DateTimeField()
    estimated_hours = models.DecimalField(
        max_digits=10, 
        decimal_places=2
    )
    state = models.CharField(
        max_length=20, 
        choices=State.choices, 
        default=State.PENDING
    )
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name