from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import mixins, serializers, viewsets
from rest_framework.response import Response

from django.db.models import Q

from api.serializers.autocomplete import (
    AutocompleteItemSerializer,
    AutocompleteRequestSerializer,
)
from api.views.filter import get_static_filter_label
from core.models import ShowroomObject


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

        allowed_filters = ['default', 'activity', 'person']
        if filter_id not in allowed_filters:
            return Response(
                {
                    'detail': f'{filter_id} is not an allowed autocomplete filter. allowed: {allowed_filters}',
                },
                status=400,
            )

        items = []
        q_filter = None
        if filter_id == 'default':
            pass
        elif filter_id == 'activity':
            q_filter = Q(type=ShowroomObject.ACTIVITY)
        elif filter_id == 'person':
            q_filter = Q(type=ShowroomObject.PERSON)

        objects = ShowroomObject.objects.filter(title__icontains=q)
        if q_filter:
            objects = objects.filter(q_filter)
        if limit:
            objects = objects[0:limit]
        for obj in objects:
            items.append(
                {
                    'id': obj.id,
                    'title': obj.title,
                    'subtext': obj.subtext,
                }
            )

        ret = [
            {
                'source': filter_id,
                'label': get_static_filter_label(filter_id, lang),
                'data': items,
            }
        ]
        return Response(ret, status=200)
