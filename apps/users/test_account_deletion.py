from types import SimpleNamespace
from unittest.mock import patch

from clerk_backend_api.models import ClerkBaseError
from django.test import TestCase
from django.utils import timezone
from httpx import ConnectError, Request, Response
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework.exceptions import AuthenticationFailed
from django.http import Http404

from apps.events.models import Event, EventType
from apps.events.services import create_event
from apps.subtasks.models import Subtask
from .authentication import ClerkAuthentication
from .models import User


def provider_error(status):
    return ClerkBaseError("provider error", Response(status, request=Request("DELETE", "https://api.clerk.test/users/owner")))


class DeleteAccountTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", clerk_id="user-owner")
        self.other = User.objects.create_user(username="other", clerk_id="user-other")
        self.kind = EventType.objects.create(name="Boda")
        self.event = self.make_event(self.owner)
        self.other_event = self.make_event(self.other)
        self.orphan = self.make_event(None)
        self.task = Subtask.objects.create(event=self.event, name="Propia", target_date=self.event.date, estimated_hours=2)
        self.other_task = Subtask.objects.create(event=self.other_event, name="Ajena", target_date=self.event.date, estimated_hours=2)
        self.client = APIClient()
        self.authenticate()
        self.patch = patch("apps.users.services.Clerk")
        self.factory = self.patch.start()
        self.addCleanup(self.patch.stop)
        self.clerk = self.factory.return_value.__enter__.return_value
        self.clerk.users.get.return_value = SimpleNamespace(delete_self_enabled=True)
        self.clerk.users.delete.return_value = SimpleNamespace(deleted=True)

    def make_event(self, user):
        return Event.objects.create(user=user, type=self.kind, name="Evento", date=timezone.now() + timezone.timedelta(days=10), location="Cali", contact="Laura")

    def authenticate(self, **claims):
        self.client.force_authenticate(self.owner, token={"sub": self.owner.clerk_id, "fva": [0, -1], **claims})

    def delete(self, **body):
        return self.client.delete("/api/auth/me/", body, format="json", HTTP_X_ACCOUNT_DELETION_CONFIRMATION="ELIMINAR")

    def assert_preserved(self):
        self.assertTrue(User.objects.filter(pk=self.owner.pk).exists())
        self.assertTrue(Event.objects.filter(pk=self.event.pk, user=self.owner).exists())
        self.assertTrue(Subtask.objects.filter(pk=self.task.pk).exists())

    def test_deletes_identity_and_all_owned_data_only(self):
        response = self.delete(user_id=self.other.pk, clerk_id=self.other.clerk_id)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")
        self.assertFalse(User.objects.filter(pk=self.owner.pk).exists())
        self.assertFalse(Event.objects.filter(pk=self.event.pk).exists())
        self.assertFalse(Subtask.objects.filter(pk=self.task.pk).exists())
        self.assertTrue(User.objects.filter(pk=self.other.pk).exists())
        self.assertTrue(Event.objects.filter(pk=self.other_event.pk).exists())
        self.assertTrue(Subtask.objects.filter(pk=self.other_task.pk).exists())
        self.assertTrue(Event.objects.filter(pk=self.orphan.pk).exists())
        self.assertTrue(EventType.objects.filter(pk=self.kind.pk).exists())
        self.clerk.users.delete.assert_called_once_with(user_id="user-owner", timeout_ms=8000, retries=None)

    def test_confirmation_is_required(self):
        for confirmation in [None, "eliminar", ""]:
            with self.subTest(confirmation=confirmation):
                headers = {} if confirmation is None else {"HTTP_X_ACCOUNT_DELETION_CONFIRMATION": confirmation}
                self.assertEqual(self.client.delete("/api/auth/me/", **headers).status_code, 400)
        self.factory.assert_not_called()
        self.assert_preserved()

    def test_requires_authentication(self):
        self.client = APIClient()
        self.assertEqual(self.delete().status_code, 401)
        self.factory.assert_not_called()
        self.assert_preserved()

    def test_rejects_identity_mismatch(self):
        self.authenticate(sub=self.other.clerk_id)
        self.assertEqual(self.delete().status_code, 403)
        self.factory.assert_not_called()
        self.assert_preserved()

    def test_requires_recent_verified_claims_before_any_writes(self):
        for ages in [None, [], [10, -1], [0, 10], [-1, -1], [True, -1], [0, "0"], [-2, -1]]:
            with self.subTest(ages=ages):
                self.authenticate(fva=ages)
                response = self.delete()
                self.assertEqual(response.status_code, 403)
                self.assertEqual(response.data["clerk_error"]["metadata"]["reverification"], "strict")
                self.assert_preserved()
        self.factory.assert_not_called()

    def test_accepts_a_recent_second_factor(self):
        self.authenticate(fva=[20, 0])
        self.assertEqual(self.delete().status_code, 204)

    def test_respects_provider_self_deletion_setting(self):
        self.clerk.users.get.return_value.delete_self_enabled = False
        self.assertEqual(self.delete().status_code, 403)
        self.clerk.users.delete.assert_not_called()
        self.assert_preserved()

    def test_provider_failure_rolls_back_user_events_and_tasks(self):
        for error in [provider_error(429), provider_error(500), ConnectError("network")]:
            with self.subTest(error=type(error).__name__):
                self.clerk.users.delete.side_effect = error
                response = self.delete()
                self.assertEqual(response.status_code, 503)
                self.assertNotIn("provider error", str(response.data))
                self.assert_preserved()
        self.clerk.users.delete.side_effect = None
        self.assertEqual(self.delete().status_code, 204)

    def test_does_not_delete_data_when_identity_lookup_fails(self):
        self.clerk.users.get.side_effect = provider_error(503)
        self.assertEqual(self.delete().status_code, 503)
        self.clerk.users.delete.assert_not_called()
        self.assert_preserved()

    def test_requires_provider_confirmation_of_deletion(self):
        self.clerk.users.delete.return_value.deleted = False
        self.assertEqual(self.delete().status_code, 503)
        self.assert_preserved()

    def test_can_finish_local_cleanup_if_identity_is_already_deleted(self):
        self.clerk.users.get.side_effect = provider_error(404)
        self.assertEqual(self.delete().status_code, 204)
        self.clerk.users.delete.assert_not_called()
        self.assertFalse(Event.objects.filter(pk=self.event.pk).exists())

    def test_concurrent_provider_deletion_is_idempotent(self):
        self.clerk.users.delete.side_effect = provider_error(404)
        self.assertEqual(self.delete().status_code, 204)
        self.assertFalse(User.objects.filter(pk=self.owner.pk).exists())

    def test_stale_user_cannot_create_orphan_events_after_deletion(self):
        self.assertEqual(self.delete().status_code, 204)
        with self.assertRaises(Http404):
            create_event(user=self.owner, validated_data={
                "name": "Evento tardío", "type": self.kind, "date": self.event.date,
                "location": "Cali", "contact": "Laura",
            })
        self.assertFalse(Event.objects.filter(name="Evento tardío").exists())


class DeletedIdentityAuthenticationTests(TestCase):
    @patch("apps.users.authentication.Clerk")
    def test_unexpired_token_cannot_recreate_a_deleted_identity(self, factory):
        clerk = factory.return_value
        clerk.authenticate_request.return_value = SimpleNamespace(is_signed_in=True, payload={"sub": "user-deleted"})
        clerk.users.get.side_effect = provider_error(404)
        request = APIRequestFactory().get("/api/auth/me/", HTTP_AUTHORIZATION="Bearer cached-token")
        with self.assertRaises(AuthenticationFailed):
            ClerkAuthentication().authenticate(request)
        self.assertFalse(User.objects.filter(clerk_id="user-deleted").exists())

    @patch("apps.users.authentication.Clerk")
    def test_first_sign_in_still_creates_a_live_identity(self, factory):
        clerk = factory.return_value
        clerk.authenticate_request.return_value = SimpleNamespace(is_signed_in=True, payload={"sub": "user-live"})
        request = APIRequestFactory().get("/api/auth/me/", HTTP_AUTHORIZATION="Bearer fresh-token")
        user, claims = ClerkAuthentication().authenticate(request)
        self.assertEqual(user.clerk_id, "user-live")
        self.assertEqual(claims["sub"], user.clerk_id)

    @patch("apps.users.authentication.Clerk")
    def test_existing_identity_does_not_require_a_second_provider_lookup(self, factory):
        owner = User.objects.create_user(username="owner", clerk_id="user-owner")
        clerk = factory.return_value
        clerk.authenticate_request.return_value = SimpleNamespace(is_signed_in=True, payload={"sub": owner.clerk_id})
        request = APIRequestFactory().get("/api/auth/me/", HTTP_AUTHORIZATION="Bearer fresh-token")
        user, _ = ClerkAuthentication().authenticate(request)
        self.assertEqual(user.pk, owner.pk)
        clerk.users.get.assert_not_called()
