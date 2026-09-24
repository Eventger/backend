from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers
from django.utils import timezone

from .models import Event, EventType

class EventTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventType
        fields = [
            "id",
            "name",
            "description",
        ]

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            "id",
            "user",
            "name",
            "type",
            "date",
            "location",
            "contact",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "created_at",
            "updated_at",
        ]

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                "El nombre del evento no puede estar vacío."
            )
        return value.strip()

    def validate_location(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                "La ubicación del evento no puede estar vacía."
            )
        return value.strip()

    def validate_date(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError(
                "La fecha del evento no puede ser anterior a la fecha actual."
            )
        return value

    def validate_contact(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "El contacto del evento no puede estar vacío."
            )

        return value


class EventResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField(required=False)
    data = EventSerializer()


@extend_schema_serializer(many=False)
class EventListResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    data = EventSerializer(many=True)


class EventTypeListResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    data = EventTypeSerializer(many=True)
