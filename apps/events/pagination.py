from django.core.paginator import Paginator
from rest_framework.pagination import BasePagination
from rest_framework.response import Response

from .serializers import EventListFilterSerializer


class EventPagination(BasePagination):
    page_size = 6

    def paginate_queryset(self, queryset, request, view=None):
        filters = EventListFilterSerializer(data=request.query_params)
        filters.is_valid(raise_exception=True)
        paginator = Paginator(queryset, self.page_size)
        # Una página eliminada o un enlace antiguo vuelve a la última disponible.
        self.page = paginator.get_page(filters.validated_data["page"])
        return list(self.page)

    def get_paginated_response(self, data):
        return Response({
            "success": True,
            "data": data,
            "pagination": {
                "page": self.page.number,
                "page_size": self.page_size,
                "total": self.page.paginator.count,
                "total_pages": self.page.paginator.num_pages,
            },
        })
