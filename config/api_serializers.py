from rest_framework import serializers


class ValidationErrorResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()
    errors = serializers.DictField()


class MessageErrorResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()


class HealthResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    service = serializers.CharField()


class IndexResponseSerializer(serializers.Serializer):
    service = serializers.CharField()
    health = serializers.CharField()
