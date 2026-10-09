from unittest.mock import Mock

from clerk_backend_api import Clerk
from clerk_backend_api.security.types import AuthenticateRequestOptions
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from apps.users.models import User
from apps.users.services import get_clerk_user

_clerk_client = None


def get_clerk_client():
    global _clerk_client
    if _clerk_client is None or isinstance(Clerk, Mock):
        client = Clerk(bearer_auth=settings.CLERK_SECRET_KEY)
        if not isinstance(Clerk, Mock):
            _clerk_client = client
        return client
    return _clerk_client


class ClerkAuthentication(BaseAuthentication):
    def authenticate_header(self, request):
        return "Bearer"

    def __init__(self, clerk=None):
        self.clerk = clerk or get_clerk_client()

    def authenticate(self, request):
        authorization = request.headers.get("Authorization")

        if not authorization:
            return None

        if not authorization.startswith("Bearer "):
            raise AuthenticationFailed("Invalid authorization header.")

        request_state = self.clerk.authenticate_request(
            request,
            AuthenticateRequestOptions(
                authorized_parties=settings.CLERK_AUTHORIZED_PARTIES,
            ),
        )

        if not request_state.is_signed_in:
            raise AuthenticationFailed("Invalid or expired Clerk token.")

        clerk_user_id = request_state.payload.get("sub")

        if not clerk_user_id:
            raise AuthenticationFailed("Clerk token does not contain a user ID.")

        user = User.objects.filter(clerk_id=clerk_user_id).first()
        if user is None:
            # Un JWT aún no vencido de una cuenta borrada no puede recrear datos.
            if get_clerk_user(self.clerk, clerk_user_id) is None:
                raise AuthenticationFailed("The Clerk account no longer exists.")
            user, _ = User.objects.get_or_create(
                clerk_id=clerk_user_id,
                defaults={
                    "username": clerk_user_id,
                },
            )

        return user, request_state.payload
