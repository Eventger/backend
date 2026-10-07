from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.exceptions import PermissionDenied

from .models import User
from .serializers import (
    PlanningPreferencesSerializer, PlanningPreferencesResponseSerializer,
    PlanningPreferencesUpdateSerializer,
    DeleteAccountSerializer, ReverificationResponseSerializer,
)
from config.api_serializers import ValidationErrorResponseSerializer, MessageErrorResponseSerializer
from .services import AccountProviderUnavailable, delete_account


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "id": request.user.id,
                "clerk_id": request.user.clerk_id,
                "username": request.user.username,
                "daily_limit_hours": request.user.daily_limit_hours,
            }
        )

    @extend_schema(
        request=None,
        parameters=[OpenApiParameter(
            name="X-Account-Deletion-Confirmation", location=OpenApiParameter.HEADER,
            required=True, type=str, enum=["ELIMINAR"],
            description="Confirmación explícita del borrado permanente de la cuenta propia.",
        )],
        responses={
            204: None, 400: ValidationErrorResponseSerializer,
            401: MessageErrorResponseSerializer, 403: ReverificationResponseSerializer,
            503: MessageErrorResponseSerializer,
        },
        description="Elimina la identidad Clerk, el organizador y sus eventos/tareas. Requiere reverificación strict y confirmación ELIMINAR.",
    )
    def delete(self, request):
        serializer = DeleteAccountSerializer(data={
            "confirmation": request.headers.get("X-Account-Deletion-Confirmation", ""),
        })
        serializer.is_valid(raise_exception=True)
        claims = request.auth if isinstance(request.auth, dict) else {}
        if not request.user.clerk_id or claims.get("sub") != request.user.clerk_id:
            raise PermissionDenied()
        ages = claims.get("fva")
        valid_ages = (
            isinstance(ages, list) and len(ages) == 2
            and all(type(age) is int and age >= -1 for age in ages)
        )
        # strict: segundo factor si está presente; primero cuando no hay segundo.
        age = (ages[1] if ages[1] != -1 else ages[0]) if valid_ages else -1
        if age < 0 or age >= 10:
            return Response({
                "success": False,
                "clerk_error": {
                    "type": "forbidden", "reason": "reverification-error",
                    "metadata": {"reverification": "strict"},
                },
            }, status=status.HTTP_403_FORBIDDEN)
        try:
            delete_account(user=request.user)
        except AccountProviderUnavailable:
            return Response({
                "success": False,
                "message": "No pudimos completar la eliminación. Inténtalo de nuevo.",
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PlanningPreferencesView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: PlanningPreferencesResponseSerializer})
    def get(self, request):
        user = User.objects.get(pk=request.user.pk)
        return Response({"success": True, "data": PlanningPreferencesSerializer(user).data})

    @extend_schema(
        request=PlanningPreferencesUpdateSerializer,
        responses={200: PlanningPreferencesResponseSerializer, 400: ValidationErrorResponseSerializer},
    )
    @transaction.atomic
    def put(self, request):
        user = User.objects.select_for_update().get(pk=request.user.pk)
        serializer = PlanningPreferencesUpdateSerializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        only_if_unconfigured = serializer.validated_data.pop("only_if_unconfigured")
        if only_if_unconfigured and user.daily_limit_configured:
            return Response({"success": True, "data": PlanningPreferencesSerializer(user).data})
        serializer.save(daily_limit_configured=True)
        return Response({"success": True, "data": serializer.data})
