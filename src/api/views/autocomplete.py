from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import mixins, serializers, viewsets
from rest_framework.response import Response

from django.db.models import Q

from api.serializers.autocomplete import (
    AutocompleteRequestSerializer,
    AutocompleteSerializer,
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
                response=serializers.ListSerializer(child=AutocompleteSerializer()),
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

        allowed_filters = ['fulltext', 'activity', 'person']
        if filter_id not in allowed_filters:
            return Response(
                {
                    'detail': f'{filter_id} is not an allowed autocomplete filter. allowed: {allowed_filters}',
                },
                status=400,
            )

        return Response(
            self.get_results(
                ShowroomObject.active_objects.all(), q, filter_id, limit, lang
            ),
            status=200,
        )

    @staticmethod
    def get_results(base_queryset, q, filter_id, limit, lang):
        q_filter = None
        if filter_id == 'fulltext':
            pass
        elif filter_id == 'activity':
            q_filter = Q(type=ShowroomObject.ACTIVITY)
        elif filter_id == 'person':
            q_filter = Q(type=ShowroomObject.PERSON)

        items_activity = []
        items_person = []
        objects = base_queryset.filter(
            title__icontains=q,
            type__in=[ShowroomObject.ACTIVITY, ShowroomObject.PERSON],
        )
        if q_filter:
            objects = objects.filter(q_filter)
        if limit:
            objects = objects[0:limit]
        for obj in objects:
            if obj.type == ShowroomObject.ACTIVITY:
                items_activity.append(
                    {
                        'id': obj.id,
                        'title': obj.title,
                        'subtext': obj.subtext,
                    }
                )
            elif obj.type == ShowroomObject.PERSON:
                items_person.append(
                    {
                        'id': obj.id,
                        'title': obj.title,
                        'subtext': obj.subtext,
                    }
                )

        ret = []
        if items_activity:
            ret.append(
                {
                    'filter_id': 'activity',
                    'label': get_static_filter_label('activity', lang),
                    'data': items_activity,
                }
            )
        if items_person:
            ret.append(
                {
                    'filter_id': 'person',
                    'label': get_static_filter_label('person', lang),
                    'data': items_person,
                }
            )
        return ret
