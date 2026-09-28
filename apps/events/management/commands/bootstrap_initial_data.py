from django.core.management.base import BaseCommand
from django.db import transaction

from apps.events.models import EventType


INITIAL_EVENT_TYPES = [
    ("Boda", "Evento de boda."),
    ("Social", "Evento social."),
    ("Corporativo", "Evento corporativo."),
    ("Cumpleaños", "Evento de cumpleaños."),
    ("Otro", "Otro tipo de evento."),
]


class Command(BaseCommand):
    help = "Crea el catálogo inicial de tipos de evento."

    @transaction.atomic
    def handle(self, *args, **options):
        created_types = 0

        for name, description in INITIAL_EVENT_TYPES:
            _, created = EventType.objects.get_or_create(
                name=name,
                defaults={"description": description},
            )
            created_types += int(created)

        self.stdout.write(
            self.style.SUCCESS(
                f"Bootstrap completado: {created_types} tipos creados."
            )
        )