from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers
from .models import Subtask

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

class TodayDataSerializer(serializers.Serializer):
    overdue = SubtaskSerializer(many=True)
    today = SubtaskSerializer(many=True)
    upcoming = SubtaskSerializer(many=True)
    completed = SubtaskSerializer(many=True)


class TodayResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    data = TodayDataSerializer()