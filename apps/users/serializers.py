from rest_framework import serializers

from .models import User


class UserMeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    clerk_id = serializers.CharField(allow_null=True)
    username = serializers.CharField()
    daily_limit_hours = serializers.DecimalField(
        max_digits=4, decimal_places=2, allow_null=True
    )


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
