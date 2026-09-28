from django.contrib.auth import get_user_model

from .models import Event

User = get_user_model()


def create_event(*, user: User, validated_data):
    return Event.objects.create(
        user=user,
        **validated_data,
    )