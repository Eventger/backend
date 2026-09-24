from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User

from apps.events.models import Event
from config.api_serializers import (
    MessageErrorResponseSerializer,
    ValidationErrorResponseSerializer,
)
from config.openapi_examples import (
    SUBTASK_CREATE_EXAMPLES,
    SUBTASK_STATE_UPDATE_EXAMPLES,
)

from .models import Subtask
from .serializers import (
    SubtaskListResponseSerializer,
    SubtaskResponseSerializer,
    SubtaskSerializer,
    SubtaskUpdateSerializer,
    TodayResponseSerializer,
)
from .services import create_subtask, get_today_subtasks


class SubtaskViewSet(viewsets.GenericViewSet):
    serializer_class = SubtaskSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Subtask.objects.filter(
            event__user__username="demo",
        ).order_by("target_date")

    def get_serializer_class(self):
        if self.action in {"update", "partial_update"}:
            return SubtaskUpdateSerializer

        return SubtaskSerializer

    @extend_schema(
        responses={200: SubtaskListResponseSerializer},
    )
    def list(self, request, *args, **kwargs):
        subtasks = self.get_queryset()

        serializer = self.get_serializer(
            subtasks,
            many=True,
        )

        return Response(
            {
                "success": True,
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        responses={
            200: SubtaskResponseSerializer,
            404: MessageErrorResponseSerializer,
        },
    )
    def retrieve(self, request, *args, **kwargs):
        subtask = self.get_object()

        serializer = self.get_serializer(subtask)

        return Response(
            {
                "success": True,
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        request=SubtaskUpdateSerializer,
        responses={
            200: SubtaskResponseSerializer,
            400: ValidationErrorResponseSerializer,
            404: MessageErrorResponseSerializer,
        },
    )
    def update(self, request, *args, **kwargs):
        subtask = self.get_object()

        serializer = self.get_serializer(
            subtask,
            data=request.data,
        )

        serializer.is_valid(raise_exception=True)

        subtask = serializer.save()

        return Response(
            {
                "success": True,
                "message": "Subtarea actualizada correctamente.",
                "data": self.get_serializer(subtask).data,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        request=SubtaskUpdateSerializer,
        responses={
            200: SubtaskResponseSerializer,
            400: ValidationErrorResponseSerializer,
            404: MessageErrorResponseSerializer,
        },
        examples=SUBTASK_STATE_UPDATE_EXAMPLES,
    )
    def partial_update(self, request, *args, **kwargs):
        subtask = self.get_object()

        serializer = self.get_serializer(
            subtask,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(raise_exception=True)

        subtask = serializer.save()

        return Response(
            {
                "success": True,
                "message": "Subtarea actualizada correctamente.",
                "data": self.get_serializer(subtask).data,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        responses={
            204: OpenApiResponse(description="Subtarea eliminada correctamente."),
            404: MessageErrorResponseSerializer,
        },
    )
    def destroy(self, request, *args, **kwargs):
        subtask = self.get_object()
        subtask.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )


class EventSubtaskView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        responses={
            200: SubtaskListResponseSerializer,
            404: MessageErrorResponseSerializer,
        },
    )
    def get(self, request, event_id):
        event = Event.objects.filter(
            pk=event_id,
            user__username="demo",
        ).first()

        if event is None:
            return Response(
                {
                    "success": False,
                    "message": "El evento no existe.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        subtasks = event.subtasks.all().order_by("target_date")

        serializer = SubtaskSerializer(
            subtasks,
            many=True,
        )

        return Response(
            {
                "success": True,
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        request=SubtaskSerializer,
        responses={
            201: SubtaskResponseSerializer,
            400: ValidationErrorResponseSerializer,
            404: MessageErrorResponseSerializer,
        },
        examples=SUBTASK_CREATE_EXAMPLES,
    )
    def post(self, request, event_id):
        event = Event.objects.filter(
            pk=event_id,
            user__username="demo",
        ).first()

        if event is None:
            return Response(
                {
                    "success": False,
                    "message": "El evento no existe.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = SubtaskSerializer(
            data=request.data,
        )

        serializer.is_valid(raise_exception=True)

        subtask = create_subtask(
            event=event,
            validated_data=serializer.validated_data,
        )

        return Response(
            {
                "success": True,
                "message": "Subtarea creada correctamente.",
                "data": SubtaskSerializer(subtask).data,
            },
            status=status.HTTP_201_CREATED,
        )


class TodaySubtaskView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        responses={200: TodayResponseSerializer},
    )
    def get(self, request):
        user = User.objects.get(username="demo")

        subtasks = get_today_subtasks(
            user=user,
        )

        return Response(
            {
                "success": True,
                "data": {
                    "overdue": SubtaskSerializer(
                        subtasks["overdue"],
                        many=True,
                    ).data,
                    "today": SubtaskSerializer(
                        subtasks["today"],
                        many=True,
                    ).data,
                    "upcoming": SubtaskSerializer(
                        subtasks["upcoming"],
                        many=True,
                    ).data,
                    "completed": SubtaskSerializer(
                        subtasks["completed"],
                        many=True,
                    ).data,
                },
            },
            status=status.HTTP_200_OK,
        )