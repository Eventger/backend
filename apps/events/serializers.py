from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers
from django.utils import timezone
from django.db import transaction
from apps.users.models import User

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

    @transaction.atomic
    def update(self, instance, validated_data):
        # Mismo bloqueo que la reprogramación: no se valida un plazo obsoleto.
        if instance.user_id is not None:
            User.objects.select_for_update().get(pk=instance.user_id)
        current = Event.objects.select_for_update().get(pk=instance.pk)
        if "date" in validated_data:
            deadline = timezone.localdate(validated_data["date"])
            outside = current.subtasks.filter(target_date__date__gt=deadline).order_by("target_date", "pk")
            names = list(outside.values_list("name", flat=True)[:5])
            if names:
                raise serializers.ValidationError({"date": [
                    "La fecha del evento no puede ser anterior a la fecha límite de sus tareas. "
                    "Reprograma primero estas tareas: " + ", ".join(names) + "."
                ]})
        return super().update(current, validated_data)

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


class EventPaginationSerializer(serializers.Serializer):
    page = serializers.IntegerField(min_value=1)
    page_size = serializers.IntegerField(min_value=6, max_value=6)
    total = serializers.IntegerField(min_value=0)
    total_pages = serializers.IntegerField(min_value=1)


@extend_schema_serializer(many=False)
class EventListResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    data = EventSerializer(many=True)
    pagination = EventPaginationSerializer()


class EventListFilterSerializer(serializers.Serializer):
    page = serializers.IntegerField(min_value=1, default=1)
    type = serializers.IntegerField(min_value=1, required=False)

    def to_internal_value(self, data):
        if data.get("type") == "":
            data = data.copy()
            data.pop("type")
        return super().to_internal_value(data)


class EventTypeListResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    data = EventTypeSerializer(many=True)
