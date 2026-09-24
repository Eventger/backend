from django.contrib.auth.models import User

from .exceptions import DemoUserNotConfigured
from .models import Event

DEMO_USERNAME = "demo"

def create_event(*, validated_data):
    try:
        user = User.objects.get(username=DEMO_USERNAME)
    except User.DoesNotExist as exc:
        raise DemoUserNotConfigured from exc

    return Event.objects.create(
        user=user,
        **validated_data,
    )
