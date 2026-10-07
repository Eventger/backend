from rest_framework import serializers

from .models import User


class DeleteAccountSerializer(serializers.Serializer):
    confirmation = serializers.ChoiceField(choices=["ELIMINAR"])


class ReverificationResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    clerk_error = serializers.DictField()


class PlanningPreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["daily_limit_hours", "daily_limit_configured"]
        read_only_fields = ["daily_limit_configured"]


class PlanningPreferencesResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    data = PlanningPreferencesSerializer()


class PlanningPreferencesUpdateSerializer(PlanningPreferencesSerializer):
    only_if_unconfigured = serializers.BooleanField(default=False, write_only=True)

    class Meta(PlanningPreferencesSerializer.Meta):
        fields = [*PlanningPreferencesSerializer.Meta.fields, "only_if_unconfigured"]
