from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from apps.events.management.commands.bootstrap_initial_data import INITIAL_EVENT_TYPES
from apps.events.models import EventType


class BootstrapInitialDataCommandTests(TestCase):
    def test_bootstrap_creates_event_types(self):
        output = StringIO()

        call_command("bootstrap_initial_data", stdout=output)

        self.assertEqual(
            set(EventType.objects.values_list("name", flat=True)),
            {name for name, _ in INITIAL_EVENT_TYPES},
        )
        self.assertIn("Bootstrap completado", output.getvalue())

    def test_bootstrap_is_idempotent(self):
        call_command("bootstrap_initial_data", stdout=StringIO())
        call_command("bootstrap_initial_data", stdout=StringIO())

        self.assertEqual(EventType.objects.count(), len(INITIAL_EVENT_TYPES))
