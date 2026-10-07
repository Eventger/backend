from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers
from decimal import Decimal

from .models import Subtask
from django.utils import timezone


class SubtaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subtask
        fields = [
            "id",
            "event",
            "state",
            "name",
            "target_date",
            "estimated_hours",
            "details",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "event",
            "state",
            "created_at",
            "updated_at",
        ]

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                "El nombre de la subtarea no puede estar vacío."
            )
        return value.strip()

    def validate_estimated_hours(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Las horas estimadas deben ser mayores que 0."
            )
        return value


class SubtaskUpdateSerializer(SubtaskSerializer):
    class Meta(SubtaskSerializer.Meta):
        read_only_fields = [
            "id",
            "event",
            "created_at",
            "updated_at",
        ]


class SubtaskResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField(required=False)
    data = SubtaskSerializer()


@extend_schema_serializer(many=False)
class SubtaskListResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    data = SubtaskSerializer(many=True)

class TodaySubtaskSerializer(SubtaskSerializer):
    event_name = serializers.CharField(source="event.name", read_only=True)

    class Meta(SubtaskSerializer.Meta):
        fields = [*SubtaskSerializer.Meta.fields, "event_name"]


class TodayDataSerializer(serializers.Serializer):
    overdue = TodaySubtaskSerializer(many=True)
    today = TodaySubtaskSerializer(many=True)
    upcoming = TodaySubtaskSerializer(many=True)
    completed = TodaySubtaskSerializer(many=True)


class TodayFilterSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=Subtask.State.choices,
        required=False,
    )

    event = serializers.IntegerField(
        min_value=1,
        required=False,
    )


class TodayResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    data = TodayDataSerializer()


class OverloadConflictRequestSerializer(serializers.Serializer):
    subtask_id = serializers.IntegerField(
        min_value=1,
    )

    target_date = serializers.DateTimeField(
        required=False,
    )

    estimated_hours = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        min_value=Decimal("0.01"),
    )

    def validate(self, attrs):
        if (
            "target_date" not in attrs
            and "estimated_hours" not in attrs
        ):
            raise serializers.ValidationError(
                "Debes enviar target_date o estimated_hours."
            )

        return attrs


class OverloadConflictDataSerializer(serializers.Serializer):
    has_conflict = serializers.BooleanField()

    planned_hours = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    limit_hours = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    exceeds_by = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
    )


class OverloadConflictResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    data = OverloadConflictDataSerializer()
class ReschedulePreviewSerializer(serializers.Serializer):
    target_date = serializers.DateField()
    estimated_hours = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("0.01"), required=False)
    state = serializers.ChoiceField(choices=Subtask.State.choices, required=False)

    def validate_target_date(self, value):
        if value < timezone.localdate():
            raise serializers.ValidationError("No puedes reprogramar una tarea para una fecha anterior a hoy.")
        deadline = timezone.localdate(self.context["subtask"].event.date)
        if value > deadline:
            raise serializers.ValidationError("La fecha límite no puede ser posterior a la fecha del evento.")
        return value


class DayPlanSerializer(serializers.Serializer):
    date = serializers.DateField()
    event_date = serializers.DateField()
    existing_hours = serializers.DecimalField(max_digits=14, decimal_places=2)
    added_hours = serializers.DecimalField(max_digits=14, decimal_places=2)
    planned_hours = serializers.DecimalField(max_digits=14, decimal_places=2)
    daily_limit_hours = serializers.DecimalField(max_digits=4, decimal_places=2)
    overload_hours = serializers.DecimalField(max_digits=14, decimal_places=2)
    has_conflict = serializers.BooleanField()
    limit_hours = serializers.DecimalField(max_digits=4, decimal_places=2)
    exceeds_by = serializers.DecimalField(max_digits=14, decimal_places=2)
    tasks = serializers.ListField(child=serializers.DictField())
    suggestion = serializers.DictField(allow_null=True)


class DayPlanResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField(required=False)
    data = DayPlanSerializer()


class SubtaskPlanningResponseSerializer(SubtaskResponseSerializer):
    planning = DayPlanSerializer()
