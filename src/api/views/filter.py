from drf_spectacular.utils import extend_schema
from rest_framework import mixins, viewsets
from rest_framework.response import Response

from api import view_spec


class FilterViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Get all the available filters that can be used in search and
    autocomplete."""

    @extend_schema(
        tags=['public'],
        responses={
            200: view_spec.Responses.Filters,
        },
    )
    def list(self, request, *args, **kwargs):
        return Response({'detail': 'Not yet implemented'}, status=400)
