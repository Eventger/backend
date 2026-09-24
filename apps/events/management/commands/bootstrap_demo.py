from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.events.models import EventType
from apps.events.services import DEMO_USERNAME


INITIAL_EVENT_TYPES = [
    ("Boda", "Evento de boda."),
    ("Social", "Evento social."),
    ("Corporativo", "Evento corporativo."),
    ("Cumpleaños", "Evento de cumpleaños."),
    ("Otro", "Otro tipo de evento."),
]


class Command(BaseCommand):
    help = "Crea el usuario demo y el catálogo inicial de tipos de evento."

    @transaction.atomic
    def handle(self, *args, **options):
        user_model = get_user_model()
        demo_user, user_created = user_model.objects.get_or_create(
            username=DEMO_USERNAME,
        )

        if user_created:
            demo_user.set_unusable_password()
            demo_user.save(update_fields=["password"])

        created_types = 0
        for name, description in INITIAL_EVENT_TYPES:
            _, created = EventType.objects.get_or_create(
                name=name,
                defaults={"description": description},
            )
            created_types += int(created)

        user_status = "creado" if user_created else "existente"
        self.stdout.write(
            self.style.SUCCESS(
                f"Bootstrap completado: usuario demo {user_status}; "
                f"{created_types} tipos creados."
            )
        )
