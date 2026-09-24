from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from config.api_serializers import (
    MessageErrorResponseSerializer,
    ValidationErrorResponseSerializer,
)
from config.openapi_examples import EVENT_CREATE_EXAMPLES

from .models import Event, EventType
from .serializers import (
    EventListResponseSerializer,
    EventResponseSerializer,
    EventSerializer,
    EventTypeListResponseSerializer,
    EventTypeSerializer,
)
from .services import create_event


class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Event.objects.filter(
            user__username="demo",
        ).order_by("-date")

    @extend_schema(
        responses={200: EventListResponseSerializer},
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
        responses={
            201: EventResponseSerializer,
            400: ValidationErrorResponseSerializer,
            503: MessageErrorResponseSerializer,
        },
        examples=EVENT_CREATE_EXAMPLES,
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
        )

        serializer.is_valid(raise_exception=True)

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
        responses={
            200: EventResponseSerializer,
            404: MessageErrorResponseSerializer,
        },
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
        responses={
            200: EventResponseSerializer,
            400: ValidationErrorResponseSerializer,
            404: MessageErrorResponseSerializer,
        },
    )
    def update(self, request, *args, **kwargs):
        event = self.get_object()

        serializer = self.get_serializer(
            event,
            data=request.data,
        )

        serializer.is_valid(raise_exception=True)

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
        responses={
            200: EventResponseSerializer,
            400: ValidationErrorResponseSerializer,
            404: MessageErrorResponseSerializer,
        },
    )
    def partial_update(self, request, *args, **kwargs):
        event = self.get_object()

        serializer = self.get_serializer(
            event,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(raise_exception=True)

        event = serializer.save()

        return Response(
            {
                "success": True,
                "message": "Evento actualizado correctamente.",
                "data": EventSerializer(event).data,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        responses={
            204: OpenApiResponse(description="Evento eliminado correctamente."),
            404: MessageErrorResponseSerializer,
        },
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
        responses={200: EventTypeListResponseSerializer},
    )
    def get(self, request):
        event_types = EventType.objects.all().order_by("id")

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
