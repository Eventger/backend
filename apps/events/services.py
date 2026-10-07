from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404

from .models import Event

User = get_user_model()


@transaction.atomic
def create_event(*, user: User, validated_data):
    user = get_object_or_404(User.objects.select_for_update(), pk=user.pk)
    return Event.objects.create(
        user=user,
        **validated_data,
    )
