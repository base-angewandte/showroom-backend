from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import mixins, viewsets
from rest_framework.exceptions import ParseError
from rest_framework.response import Response

from django.db.models import Q

from api import view_spec
from api.serializers.search import SearchRequestSerializer, SearchResultSerializer
from core.models import Activity, Entity

label_results_generic = {
    'en': 'Search results',
    'de': 'Suchergebnisse',
}


class SearchViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Submit a search to Showroom."""

    serializer_class = SearchRequestSerializer

    @extend_schema(
        tags=['public'],
        responses={
            200: OpenApiResponse(
                description='',
                response=SearchResultSerializer(many=True),
            ),
            400: view_spec.Responses.Error400,
        },
    )
    def create(self, request, *args, **kwargs):
        s = self.get_serializer(data=request.data)
        s.is_valid(raise_exception=True)
        filters = s.data.get('filters')
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

        results = []
        for flt in filters:
            if flt['id'] == 'activities':
                results = filter_activities(flt['filter_values'], limit, offset, lang)

        # TODO: add other filter types
        # TODO: add consolidation of different filter type results.
        #   - reduce items found in different result sets, but increase score
        #     for result sets with the same label
        #   - limit overall result set length

        return Response(results, status=200)


def filter_activities(values, limit, offset, language):
    """Filters all showroom activities for certain text values.

    ... matches title, primary and secondary details ...

    :param values: A list of text strings to search for
    :param limit: Maximum amount of activities to return
    :param offset: The 0-indexed offset of the first activity in the result set
    :return: A list of activities that have been found based on filter values
    """
    queryset = Activity.objects.all()
    # TODO: discuss what the ordering criteria are
    queryset = queryset.order_by('-date_created')

    for idx, value in enumerate(values):
        if type(value) is not str:
            raise ParseError(
                'Only strings are allowed for activities/persons/locations filters',
                400,
            )
        if idx == 0:
            # TODO: find reasonable filter condition
            q_filter = Q(source_repo_data_text__icontains=value)
        else:
            q_filter = q_filter | Q(source_repo_data_text__icontains=value)
    if len(value) > 0:
        queryset = queryset.filter(q_filter)

    found_activities_count = queryset.count()

    if limit is not None:
        end = offset + limit
        queryset = queryset[offset:end]
    elif offset > 0:
        queryset = queryset[offset:]

    results = []
    for activity in queryset:
        item = {
            'id': activity.id,
            'alternative_text': [],  # TODO
            'media_url': None,  # TODO
            'source_institution': {  # TODO
                'label': None,
                'url': None,
                'icon': None,
            },
            'score': 1,  # TODO
            'title': activity.title,
            'type': 'activity',  # TODO: use translated labels
        }
        results.append(item)

    # in case we found less activities than the supplied limits, we extend the
    # search to entities, that relate to the found activities
    if (num_results := len(results)) < limit:
        queryset = Entity.objects.all()
        # TODO: discuss what the ordering criteria are
        queryset = queryset.order_by('-date_created')
        if len(value) > 0:
            queryset = queryset.filter(q_filter)

        # if we already found some activities (but not enough for the limit), we start
        # we want to take entities from the start of the filtered entities.
        # otherwise the offset points behind the last activities, so we have to
        # subtract the total number of filtered activities from the offset to know
        # which is the first fount entity to be included in the result
        if num_results > 0:
            remainder_offset = 0
        else:
            remainder_offset = offset - found_activities_count

        if limit is not None:
            remainder_end = limit - num_results
            queryset = queryset[remainder_offset:remainder_end]
        elif offset > 0:
            queryset[offset:]

        for entity in queryset:
            item = {
                'id': entity.id,
                'alternative_text': [],  # TODO
                'media_url': None,  # TODO
                'source_institution': {  # TODO
                    'label': None,
                    'url': None,
                    'icon': None,
                },
                'score': 1,  # TODO
                'title': entity.title,
                'type': entity.type,  # TODO: use translated labels
            }
            results.append(item)

    return {
        'label': label_results_generic.get(language),
        'total': len(results),
        'data': results,
    }


def search_all_showroom_objects(filters, limit, offset):
    _l1, activities = search_activities(filters, limit, offset)
    _l2, persons = search_persons(filters, limit, offset)
    results = []
    results.extend(activities)
    results.extend(persons)
    return ('Search results', results)


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
                        q_filter = Q(source_repo_data_text__icontains=value)
                    else:
                        q_filter = q_filter | Q(source_repo_data_text__icontains=value)
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
