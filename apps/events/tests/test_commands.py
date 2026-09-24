from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from apps.events.management.commands.bootstrap_demo import INITIAL_EVENT_TYPES
from apps.events.models import EventType
from apps.events.services import DEMO_USERNAME


class BootstrapDemoCommandTests(TestCase):
    def test_bootstrap_creates_demo_user_and_event_types(self):
        output = StringIO()

        call_command("bootstrap_demo", stdout=output)

        demo_user = get_user_model().objects.get(username=DEMO_USERNAME)
        self.assertFalse(demo_user.has_usable_password())
        self.assertEqual(
            set(EventType.objects.values_list("name", flat=True)),
            {name for name, _ in INITIAL_EVENT_TYPES},
        )
        self.assertIn("Bootstrap completado", output.getvalue())

    def test_bootstrap_is_idempotent(self):
        call_command("bootstrap_demo", stdout=StringIO())
        call_command("bootstrap_demo", stdout=StringIO())

        self.assertEqual(
            get_user_model().objects.filter(username=DEMO_USERNAME).count(),
            1,
        )
        self.assertEqual(EventType.objects.count(), len(INITIAL_EVENT_TYPES))
