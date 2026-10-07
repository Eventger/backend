from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from django.utils import timezone
from datetime import datetime, time
from apps.users.models import User

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
    TodayFilterSerializer,
    TodayResponseSerializer,
    OverloadConflictRequestSerializer,
    OverloadConflictResponseSerializer,
    TodaySubtaskSerializer,
    ReschedulePreviewSerializer,
    DayPlanResponseSerializer,
    SubtaskPlanningResponseSerializer,
)
from .services import create_subtask, get_today_subtasks, check_daily_overload
from .planning import daily_plan, save_planning_update, SchedulingConflict


class SubtaskViewSet(viewsets.GenericViewSet):
    serializer_class = SubtaskSerializer

    @extend_schema(
        request=ReschedulePreviewSerializer,
        responses={200: DayPlanResponseSerializer, 400: ValidationErrorResponseSerializer, 404: MessageErrorResponseSerializer},
        description="Vista previa sin escrituras. Suma gestiones pendientes de todos los eventos del organizador en Bogotá.",
    )
    @action(detail=True, methods=["post"], url_path="reschedule-preview")
    def reschedule_preview(self, request, pk=None):
        subtask = self.get_object()
        serializer = ReschedulePreviewSerializer(data=request.data, context={"subtask": subtask})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        target_date = timezone.make_aware(datetime.combine(data["target_date"], time(23, 59)))
        organizer = User.objects.get(pk=request.user.pk)
        plan = daily_plan(
            user=organizer, subtask=subtask, target_date=target_date,
            estimated_hours=data.get("estimated_hours", subtask.estimated_hours), state=data.get("state"),
        )
        return Response({"success": True, "data": plan})

    def save_update(self, serializer, request):
        try:
            subtask, plan = save_planning_update(serializer=serializer, user=request.user)
        except SchedulingConflict as exc:
            return Response({
                "success": False,
                "message": f"Quedarías con {exc.plan['planned_hours']} h planificadas (límite {exc.plan['daily_limit_hours']} h).",
                "data": exc.plan,
            }, status=status.HTTP_409_CONFLICT)
        return Response({
            "success": True, "message": "Subtarea actualizada correctamente.",
            "data": self.get_serializer(subtask).data, "planning": plan,
        })

    def get_queryset(self):
        return Subtask.objects.filter(
            event__user=self.request.user,
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
            200: SubtaskPlanningResponseSerializer,
            400: ValidationErrorResponseSerializer,
            404: MessageErrorResponseSerializer,
            409: DayPlanResponseSerializer,
        },
    )
    def update(self, request, *args, **kwargs):
        subtask = self.get_object()

        serializer = self.get_serializer(
            subtask,
            data=request.data,
        )

        serializer.is_valid(raise_exception=True)

        return self.save_update(serializer, request)

    @extend_schema(
        request=SubtaskUpdateSerializer,
        responses={
            200: SubtaskPlanningResponseSerializer,
            400: ValidationErrorResponseSerializer,
            404: MessageErrorResponseSerializer,
            409: DayPlanResponseSerializer,
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

        return self.save_update(serializer, request)

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

    @extend_schema(
        responses={
            200: SubtaskListResponseSerializer,
            404: MessageErrorResponseSerializer,
        },
    )
    def get(self, request, event_id):
        event = Event.objects.filter(
            pk=event_id,
            user=self.request.user,
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
            user=self.request.user,
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

    @extend_schema(
        responses={200: TodayResponseSerializer},
        parameters=[
            OpenApiParameter(
                name="status",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                enum=[choice.value for choice in Subtask.State],
                description="Filtra por estado de la subtarea.",
            ),
            OpenApiParameter(
                name="event",
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filtra por el ID del evento.",
            ),
        ],
    )
    def get(self, request):

        filters = TodayFilterSerializer(data=request.query_params)
        filters.is_valid(raise_exception=True)

        subtasks = get_today_subtasks(
            user=request.user,
            status=filters.validated_data.get("status"),
            event_id=filters.validated_data.get("event"),
        )

        return Response(
            {
                "success": True,
                "data": {
                    "overdue": TodaySubtaskSerializer(
                        subtasks["overdue"],
                        many=True,
                    ).data,
                    "today": TodaySubtaskSerializer(
                        subtasks["today"],
                        many=True,
                    ).data,
                    "upcoming": TodaySubtaskSerializer(
                        subtasks["upcoming"],
                        many=True,
                    ).data,
                    "completed": TodaySubtaskSerializer(
                        subtasks["completed"],
                        many=True,
                    ).data,
                },
            },
            status=status.HTTP_200_OK,
        )

class OverloadConflictView(APIView):

    @extend_schema(
        request=OverloadConflictRequestSerializer,
        responses={
            200: OverloadConflictResponseSerializer,
            400: ValidationErrorResponseSerializer,
            404: MessageErrorResponseSerializer,
        },
    )
    def post(self, request):

        serializer = OverloadConflictRequestSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        subtask = Subtask.objects.filter(
            id=serializer.validated_data["subtask_id"],
            event__user=request.user,
        ).first()

        if subtask is None:
            return Response(
                {
                    "success": False,
                    "message": "La subtarea no existe.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        conflict = check_daily_overload(
            user=request.user,
            subtask=subtask,
            target_date=serializer.validated_data.get(
                "target_date"
            ),
            estimated_hours=serializer.validated_data.get(
                "estimated_hours"
            ),
        )

        response_serializer = OverloadConflictResponseSerializer(
            {
                "success": True,
                "data": conflict,
            }
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )
