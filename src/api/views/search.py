from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import mixins, viewsets
from rest_framework.exceptions import ParseError
from rest_framework.response import Response

from django.db.models import Q

from api import view_spec
from api.serializers.search import SearchCollectionSerializer, SearchRequestSerializer
from core.models import Activity


class SearchViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Submit a search to Showroom."""

    serializer_class = SearchRequestSerializer

    @extend_schema(
        tags=['public'],
        responses={
            200: OpenApiResponse(
                description='',
                response=SearchCollectionSerializer,
            ),
            400: view_spec.Responses.Error400,
        },
    )
    def create(self, request, *args, **kwargs):
        s = self.get_serializer(data=request.data)
        s.is_valid(raise_exception=True)
        filters = s.data.get('filters')
        category = s.data.get('category')
        limit = s.data.get('limit')
        offset = s.data.get('offset')
        lang = request.LANGUAGE_CODE

        if offset is None:
            offset = 0
        elif offset < 0:
            return Response({'detail': 'negative offset not allowed'}, status=400)
        if limit is not None and limit < 1:
            return Response(
                {'detail': 'negative or zero limit not allowed'}, status=400
            )

        if not category:
            label, results = search_all_showroom_objects(filters, limit, offset)
        elif category == 'activities':
            label, results = search_activities(filters, limit, offset)
        else:
            label, results = search_persons(filters, limit, offset)

        response = {
            'label': label,
            'total': len(results),
            'data': [],
        }
        for activity in results:
            activity_type = '' if not activity.type else activity.type['label'][lang]
            item = {
                'id': activity.id,
                'type': 'activity',
                'date_created': activity.date_created,
                'title': activity.title,
                'description': activity_type,
                'imageUrl': '',
                'href': '',
                'previews': [],
            }
            response['data'].append(item)
        return Response(response, status=200)


def search_all_showroom_objects(filters, limit, offset):
    return ('Filter is not yet implemented', [])


def search_activities(filters, limit, offset):
    if not filters:
        queryset = Activity.objects.all()
        # TODO: discuss what the ordering criteria are
        queryset = queryset.order_by('-date_created')
        if limit is not None:
            end = offset + limit
            queryset = queryset[offset:end]
        elif offset > 0:
            queryset = queryset[offset:]
        return ('Current activities', queryset)

    else:
        queryset = Activity.objects.all()
        # TODO: discuss what the ordering criteria are
        queryset = queryset.order_by('-date_created')

        for flt in filters:

            if flt['id'] in ['activities', 'persons', 'locations']:
                for idx, value in enumerate(flt['filter_values']):
                    if type(value) is not str:
                        raise ParseError(
                            'Only strings are allowed for activities/persons/locations filters',
                            400,
                        )
                    if idx == 0:
                        # TODO: find reasonable filter condition
                        q_filter = Q(primary_details__contains=value)
                    else:
                        q_filter = q_filter | Q(primary_details__contains=value)
                queryset = queryset.filter(q_filter)

            if flt['id'] == 'type':
                for idx, value in enumerate(flt['filter_values']):
                    if type(value) is not dict:
                        raise ParseError('Malformed keyword filter', 400)
                    if not (typ := value.get('id')):
                        raise ParseError('Malformed keyword filter', 400)
                    if type(typ) is not str:
                        raise ParseError('Malformed keyword filter', 400)
                    if idx == 0:
                        q_filter = Q(type__label__contains={'en': typ})
                    else:
                        # TODO: check why this is not working
                        q_filter = q_filter | Q(type__label__contains={'en': typ})
                    queryset = queryset.filter(q_filter)

            if flt['id'] == 'keywords':
                for idx, value in enumerate(flt['filter_values']):
                    if type(value) is not dict:
                        raise ParseError('Malformed keyword filter', 400)
                    if not (kw := value.get('id')):
                        raise ParseError('Malformed keyword filter', 400)
                    if type(kw) is not str:
                        raise ParseError('Malformed keyword filter', 400)
                    if idx == 0:
                        q_filter = Q(keywords__has_key=kw)
                    else:
                        # TODO: check why this is not working
                        q_filter = q_filter | Q(keywords__has_key=kw)
                    queryset = queryset.filter(q_filter)

        if limit is not None:
            end = offset + limit
            queryset = queryset[offset:end]
        elif offset > 0:
            queryset = queryset[offset:]
        return ('Activities', queryset)


def search_persons(filters, limit, offset):
    return ('Filter is not yet implemented', [])
