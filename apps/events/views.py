from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import EventType
from .serializers import EventSerializer, EventTypeSerializer
from .services import create_event


class EventCreateView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=EventSerializer,
        responses={201: EventSerializer},
    )
    def post(self, request):
        serializer = EventSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        event = create_event(
            validated_data=serializer.validated_data,
        )

        return Response(
            {
                "success": True,
                "message": "Evento creado correctamente.",
                "data": EventSerializer(event).data,
            },
            status=status.HTTP_201_CREATED,
        )


class EventTypeListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        responses={200: EventTypeSerializer(many=True)},
    )
    def get(self, request):
        event_types = EventType.objects.all().order_by("name")
        serializer = EventTypeSerializer(event_types, many=True)

        return Response(
            {
                "success": True,
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )