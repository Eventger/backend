from clerk_backend_api import Clerk
from clerk_backend_api.models import ClerkBaseError
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from httpx import RequestError
from rest_framework.exceptions import APIException, PermissionDenied

from apps.events.models import Event
from .models import User


class AccountProviderUnavailable(APIException):
    status_code = 503
    default_detail = "No pudimos completar la eliminación. Inténtalo de nuevo."


def get_clerk_user(clerk, clerk_id):
    try:
        return clerk.users.get(user_id=clerk_id, timeout_ms=8000, retries=None)
    except ClerkBaseError as exc:
        if exc.status_code == 404:
            return None
        raise AccountProviderUnavailable() from exc
    except RequestError as exc:
        raise AccountProviderUnavailable() from exc


@transaction.atomic
def delete_account(*, user):
    """Borra sólo el organizador autenticado; un rechazo de Clerk revierte la BD."""
    owner = get_object_or_404(User.objects.select_for_update(), pk=user.pk)
    with Clerk(bearer_auth=settings.CLERK_SECRET_KEY) as clerk:
        identity = get_clerk_user(clerk, owner.clerk_id)
        if identity is not None and not identity.delete_self_enabled:
            raise PermissionDenied("La eliminación de cuenta no está habilitada.")
        clerk_id = owner.clerk_id
        # Event.user usa SET_NULL: borrar explícitamente eventos evita huérfanos.
        # Subtask.event usa CASCADE, por lo que incluye todas las tareas propias.
        Event.objects.filter(user=owner).delete()
        owner.delete()
        if identity is not None:
            try:
                result = clerk.users.delete(user_id=clerk_id, timeout_ms=8000, retries=None)
                if not result.deleted:
                    raise AccountProviderUnavailable()
            except ClerkBaseError as exc:
                # Reintento cuando una solicitud anterior ya eliminó la identidad.
                if exc.status_code != 404:
                    raise AccountProviderUnavailable() from exc
            except RequestError as exc:
                raise AccountProviderUnavailable() from exc
