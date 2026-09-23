from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.events.models import Event

from .serializers import SubtaskSerializer
from .services import create_subtask

class SubtaskCreateView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=SubtaskSerializer,
        responses={201: SubtaskSerializer},
    )
    def post(self, request, event_id):
        try:
            event = Event.objects.get(pk=event_id)
        except Event.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "El evento no existe.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = SubtaskSerializer(data=request.data)

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
            validated_data=serializer.validated_data
        )

        return Response(
            {
                "success": True,
                "message": "Subtarea creada correctamente.",
                "data": SubtaskSerializer(subtask).data,
            },
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        responses={200: SubtaskSerializer(many=True)},
    )
    def get(self, request, event_id):
        try:
            event = Event.objects.get(
                pk=event_id,
                user__username="demo",
            )
        except Event.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "El evento no existe.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        subtasks = event.subtasks.all().order_by("-target_date")

        serializer = SubtaskSerializer(subtasks, many=True)

        return Response(
            {
                "success": True,
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )