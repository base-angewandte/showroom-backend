from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import mixins, serializers, viewsets
from rest_framework.response import Response

from api.serializers.autocomplete import (
    AutocompleteItemSerializer,
    AutocompleteRequestSerializer,
)
from api.views.filter import get_static_filter_label
from core.models import Activity


class AutocompleteViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Retrieves available autocomplete results for a specific string and
    filter."""

    # TODO: create serializer module (only quick fix to get rid of error for now)
    serializer_class = AutocompleteRequestSerializer

    @extend_schema(
        tags=['public'],
        responses={
            200: OpenApiResponse(
                description='',
                response=serializers.ListSerializer(child=AutocompleteItemSerializer()),
                # TODO: add description and examples
            ),
        },
    )
    def create(self, request, *args, **kwargs):
        s = self.get_serializer(data=request.data)
        s.is_valid(raise_exception=True)
        q = s.data.get('q')
        filter_id = s.data.get('filter_id')
        limit = s.data.get('limit')
        lang = request.LANGUAGE_CODE

        items = []
        # for now the default filter is the same as activities
        # TODO: change, as soon as we have entities and albums in our test data
        if filter_id == 'activities' or filter_id == 'default':
            activities = Activity.objects.filter(title__icontains=q)
            if limit:
                activities = activities[0:limit]
            for activity in activities:
                items.append(
                    {
                        'id': activity.id,
                        'title': activity.title,
                        'subtitle': activity.subtext,
                    }
                )

        else:
            return Response(
                {
                    'source': filter_id,
                    'label': 'This autocomplete filter is not implemented yet',
                    'data': [],
                },
                status=200,
            )

        ret = [
            {
                'source': filter_id,
                'label': get_static_filter_label(filter_id, lang),
                'data': items,
            }
        ]
        return Response(ret, status=200)
