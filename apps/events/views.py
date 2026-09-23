from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Event, EventType
from .serializers import EventSerializer, EventTypeSerializer
from .services import create_event


class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Event.objects.filter(
            user__username="demo",
        ).order_by("-date")

    @extend_schema(
        responses={200: EventSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        events = self.get_queryset()

        serializer = self.get_serializer(
            events,
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
        request=EventSerializer,
        responses={201: EventSerializer},
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
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

    @extend_schema(
        responses={200: EventSerializer},
    )
    def retrieve(self, request, *args, **kwargs):
        event = self.get_object()

        serializer = self.get_serializer(event)

        return Response(
            {
                "success": True,
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        request=EventSerializer,
        responses={200: EventSerializer},
    )
    def update(self, request, *args, **kwargs):
        event = self.get_object()

        serializer = self.get_serializer(
            event,
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

        event = serializer.save()

        return Response(
            {
                "success": True,
                "message": "Evento actualizado correctamente.",
                "data": self.get_serializer(event).data,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        request=EventSerializer,
        responses={200: EventSerializer},
    )
    def partial_update(self, request, *args, **kwargs):
        event = self.get_object()

        serializer = self.get_serializer(
            event,
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

        event = serializer.save()

        return Response(
            {
                "success": True,
                "message": "Evento actualizado correctamente.",
                "data": EventSerializer(event).data,
            },
            status=status.HTTP_200_OK,
        )

    def destroy(self, request, *args, **kwargs):
        event = self.get_object()
        event.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )


class EventTypeListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        responses={200: EventTypeSerializer(many=True)},
    )
    def get(self, request):
        event_types = EventType.objects.all().order_by("name")

        serializer = EventTypeSerializer(
            event_types,
            many=True,
        )

        return Response(
            {
                "success": True,
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )