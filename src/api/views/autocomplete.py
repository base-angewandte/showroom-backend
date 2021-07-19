from drf_spectacular.utils import extend_schema
from rest_framework import mixins, viewsets
from rest_framework.response import Response

from api import view_spec


class AutocompleteViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Retrieves available autocomplete results for a specific string and
    filter."""

    @extend_schema(
        tags=['public'],
        responses={
            200: view_spec.Responses.AutoComplete,
        },
    )
    def create(self, request, *args, **kwargs):
        return Response({'detail': 'Not yet implemented'}, status=400)
