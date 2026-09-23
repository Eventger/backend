from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.events.models import Event

from .models import Subtask
from .serializers import SubtaskSerializer
from .services import create_subtask


class SubtaskViewSet(viewsets.ModelViewSet):
    serializer_class = SubtaskSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Subtask.objects.filter(
            event__user__username="demo",
        ).order_by("target_date")

    @extend_schema(
        responses={200: SubtaskSerializer(many=True)},
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
        responses={200: SubtaskSerializer},
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
        request=SubtaskSerializer,
        responses={200: SubtaskSerializer},
    )
    def update(self, request, *args, **kwargs):
        subtask = self.get_object()

        serializer = self.get_serializer(
            subtask,
            data=request.data,
        )

        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

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
        request=SubtaskSerializer,
        responses={200: SubtaskSerializer},
    )
    def partial_update(self, request, *args, **kwargs):
        subtask = self.get_object()

        serializer = self.get_serializer(
            subtask,
            data=request.data,
            partial=True,
        )

        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        subtask = serializer.save()

        return Response(
            {
                "success": True,
                "message": "Subtarea actualizada correctamente.",
                "data": self.get_serializer(subtask).data,
            },
            status=status.HTTP_200_OK,
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
        responses={200: SubtaskSerializer(many=True)},
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
        responses={201: SubtaskSerializer},
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

        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

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