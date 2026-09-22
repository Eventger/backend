from django.contrib.auth.models import User
from .models import Event

DEMO_USERNAME = "demo"

def create_event(*, validated_data):
    user = User.objects.get(username=DEMO_USERNAME)

    return Event.objects.create(
        user=user,
        **validated_data,
    )