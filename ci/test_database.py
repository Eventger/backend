"""Contrato de infraestructura; no valida dominio ni conexión con Supabase."""
from django.contrib.auth.models import Group
from django.db import connection
from django.test import TestCase


class IsolatedPostgresTests(TestCase):
    def test_runner_uses_separate_postgresql_database(self):
        self.assertEqual(connection.vendor, "postgresql")
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database()")
            self.assertEqual(cursor.fetchone()[0], "test_eventger_ci")

    def test_django_migrations_support_database_writes(self):
        group = Group.objects.create(name="synthetic-ci-group")
        self.assertEqual(Group.objects.get(pk=group.pk).name, "synthetic-ci-group")
