import re
from datetime import date, timedelta

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import mixins, viewsets
from rest_framework.exceptions import ParseError
from rest_framework.response import Response

from django.conf import settings
from django.contrib.postgres.search import SearchQuery
from django.db.models import Q

from api import view_spec
from api.repositories.portfolio.search import get_search_item
from api.serializers.search import SearchRequestSerializer, SearchResultSerializer
from core.models import Activity, Entity

label_results_generic = {
    'en': 'Search results',
    'de': 'Suchergebnisse',
}
label_current_activities = {
    'en': 'Current activities',
    'de': 'Aktuelle Aktivitäten',
}


class SearchViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Submit a search to Showroom."""

    serializer_class = SearchRequestSerializer

    @extend_schema(
        tags=['public'],
        responses={
            200: OpenApiResponse(
                description='',
                response=SearchResultSerializer,
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
        if limit is None:
            limit = settings.SEARCH_LIMIT

        results = []
        for flt in filters:
            # for now the default filter is the same as activities
            # TODO: change, as soon as we have entities and albums in our test data
            if flt['id'] == 'activities' or flt['id'] == 'default':
                results.append(
                    filter_activities(flt['filter_values'], limit, offset, lang)
                )
            if flt['id'] == 'type':
                results.append(filter_type(flt['filter_values'], limit, offset, lang))
            if flt['id'] == 'keywords':
                results.append(
                    filter_keywords(flt['filter_values'], limit, offset, lang)
                )
            if flt['id'] == 'current_activities':
                results.append(
                    filter_current_activities(flt['filter_values'], limit, offset, lang)
                )
            if flt['id'] == 'start_page':
                # as we have no user specific start page filters yet in v1.0, we can
                # just return the current activities result set
                results.append(
                    filter_current_activities(flt['filter_values'], limit, offset, lang)
                )
            if flt['id'] == 'date':
                results.append(filter_date(flt['filter_values'], limit, offset, lang))
            if flt['id'] == 'daterange':
                results.append(
                    filter_daterange(flt['filter_values'], limit, offset, lang)
                )

        # TODO: discuss if/how search result consolidation should happen
        #       will probably mostly depend on scoring, so dicuss scoring as well
        if len(results) == 1:
            return Response(results[0], status=200)
        else:
            consolidated_label = 'Consolidated search results: ' + ', '.join(
                [r['label'] for r in results]
            )
            consolidated_results = []
            ids = []
            total = 0
            for idx, r in enumerate(results):
                if idx == 0:
                    consolidated_results.extend(r['data'])
                    ids.extend([r['id'] for r in consolidated_results])
                    total += r['total']
                else:
                    # filter out duplicates before processing the result set
                    for i, item in enumerate(r['data']):
                        if item['id'] in ids:
                            r['data'].pop(i)
                    # now add the total and as many items as needed to fill the limit
                    # TODO: something still seems to be off with the total in cases
                    #       where the limit is significantly lower than the total
                    total += len(r['data'])
                    for item in r['data']:
                        ids.append(item['id'])
                        if len(consolidated_results) < limit:
                            consolidated_results.append(item)

            return Response(
                {
                    'label': consolidated_label,
                    'total': total,
                    'data': consolidated_results,
                },
                status=200,
            )


def filter_activities(values, limit, offset, language):
    """Filters all showroom activities for certain text values.

    Does a very generic (TBD) search on activities and related entities. The results
    are paginated by limit and offset values, but a total count for all found
    entities and activities will always be returned in the result.

    :param values: A list of text strings to search for
    :param limit: Maximum amount of activities to return
    :param offset: The 0-indexed offset of the first activity in the result set
    :return: A SearchResult dictionary, as defined in the API spec.
    """
    activities_queryset = Activity.objects.all()
    # TODO: discuss what the ordering criteria are
    activities_queryset = activities_queryset.order_by('-date_created')

    if not values:
        raise ParseError('Activities filter needs at least one value', 400)

    q_filter = None
    for _idx, value in enumerate(values):
        if type(value) is not str:
            raise ParseError(
                'Only strings are allowed for activities/persons/locations/default filters',
                400,
            )
        # TODO: quick fix for multi word FTS, as long as concrete search algo is not discussed
        words = re.findall(r'[\w]+', value)
        if not words:
            raise ParseError(
                f'The value "{value}" does not contain any valid search words',
                400,
            )

        for word in words:
            if q_filter is None:
                q_filter = Q(
                    activitysearch__language=language,
                    activitysearch__text_vector=SearchQuery(
                        word + ':*', config='simple', search_type='raw'
                    ),
                )
            else:
                q_filter = q_filter | Q(
                    activitysearch__language=language,
                    activitysearch__text_vector=SearchQuery(
                        word + ':*', config='simple', search_type='raw'
                    ),
                )
    if len(values) > 0:
        activities_queryset = activities_queryset.filter(q_filter)

    found_activities_count = activities_queryset.count()

    # Before we apply any pagination, we also search through all related entities, to
    # get their total count as well.

    entities_queryset = Entity.objects.all()
    # TODO: discuss what the ordering criteria are
    entities_queryset = entities_queryset.order_by('-date_created')
    if len(values) > 0:
        # TODO: this might be more efficient by just querying for all entities
        #   with their ids taken from the activities result set above. especially
        #   when the query becomes more complex.
        q_filter = None
        for _idx, value in enumerate(values):
            words = re.findall(r'[\w]+', value)
            if q_filter is None:
                q_filter = Q(
                    activity__activitysearch__language=language,
                    activity__activitysearch__text_vector=SearchQuery(
                        word + ':*', config='simple', search_type='raw'
                    ),
                )
            else:
                q_filter = q_filter | Q(
                    activity__activitysearch__language=language,
                    activity__activitysearch__text_vector=SearchQuery(
                        word + ':*', config='simple', search_type='raw'
                    ),
                )

        entities_queryset = entities_queryset.filter(q_filter).distinct()

    found_entities_count = entities_queryset.count()

    end = offset + limit
    activities_queryset = activities_queryset[offset:end]

    results = [get_search_item(activity, language) for activity in activities_queryset]

    num_results = len(results)

    # in case we found less activities than the supplied limits, we extend the list
    # by the related entities from the entities_queryset
    if num_results < limit:

        # if we already found some activities (but not enough for the limit),
        # we want to take entities from the start of the filtered entities.
        # otherwise the offset points behind the last activities, so we have to
        # subtract the total number of filtered activities from the offset to know
        # which is the first fount entity to be included in the result
        if num_results > 0:
            remainder_offset = 0
        else:
            remainder_offset = offset - found_activities_count

        remainder_end = limit - num_results
        entities_queryset = entities_queryset[remainder_offset:remainder_end]

        results.extend(
            [get_search_item(entity, language) for entity in entities_queryset]
        )

    return {
        'label': label_results_generic.get(language),
        'total': found_activities_count + found_entities_count,
        'data': results,
    }


def filter_current_activities(values, limit, offset, language):
    # TODO: discuss: should values and offset for this filter just be ignored?
    # TODO: the whole query might still be combined into a sinqle query with
    #       Case, When and annotations, to generate a more useful ranking.
    #       See: https://www.vinta.com.br/blog/2017/advanced-django-querying-sorting-events-date/

    activities_queryset = Activity.objects.all()
    today = date.today()
    future_limit = today + timedelta(days=settings.CURRENT_ACTIVITIES_FUTURE)
    past_limit = today - timedelta(days=settings.CURRENT_ACTIVITIES_PAST)

    today_activities = activities_queryset.filter(activitysearchdates__date=today)
    today_count = today_activities.count()
    future_activities = (
        activities_queryset.filter(
            (
                Q(activitysearchdates__date__gt=today)
                & Q(activitysearchdates__date__lte=future_limit)
            )
            | (
                Q(activitysearchdateranges__date_from__lte=today)
                & Q(activitysearchdateranges__date_to__gt=today)
            )
        )
        .exclude(activitysearchdates__date=today)
        .distinct()
    )
    future_count = future_activities.count()
    past_activities = (
        activities_queryset.filter(
            (
                Q(activitysearchdates__date__lt=today)
                & Q(activitysearchdates__date__gte=past_limit)
            )
            | (
                Q(activitysearchdateranges__date_from__lt=today)
                & Q(activitysearchdateranges__date_to__gte=today)
            )
        )
        .exclude(activitysearchdates__date=today)
        .exclude(
            (
                Q(activitysearchdates__date__gt=today)
                & Q(activitysearchdates__date__lte=future_limit)
            )
            | (
                Q(activitysearchdateranges__date_from__lte=today)
                & Q(activitysearchdateranges__date_to__gt=today)
            )
        )
    )
    past_count = past_activities.count()

    if today_count >= limit:
        final = [
            get_search_item(activity, language)
            for activity in today_activities[0:limit]
        ]
    else:
        final = [get_search_item(activity, language) for activity in today_activities]
        if today_count + future_count >= limit:
            final.extend(
                [
                    get_search_item(activity, language)
                    for activity in future_activities[0 : limit - today_count]
                ]
            )
        else:
            final.extend(
                [get_search_item(activity, language) for activity in future_activities]
            )
            if today_count + future_count + past_count >= limit:
                final.extend(
                    [
                        get_search_item(activity, language)
                        for activity in past_activities[
                            0 : limit - today_count - future_count
                        ]
                    ]
                )
            else:
                final.extend(
                    [
                        get_search_item(activity, language)
                        for activity in past_activities
                    ]
                )

    return {
        'label': label_current_activities.get(language),
        'total': today_count + future_count + past_count,
        'data': final,
    }


def filter_date(values, limit, offset, language):
    if not values:
        raise ParseError('Date filter needs at least one value', 400)

    flt = None
    for value in values:
        if type(value) is not str:
            raise ParseError(
                'Only strings are allowed as date filter values',
                400,
            )
        if not re.match(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$', value):
            raise ParseError(
                'Only dates of format YYYY-MM-DD can be used as date filter values',
                400,
            )
        add_flt = Q(activitysearchdates__date=value) | (
            Q(activitysearchdateranges__date_from__lte=value)
            & Q(activitysearchdateranges__date_to__gte=value)
        )
        if not flt:
            flt = add_flt
        else:
            flt = flt | add_flt

    activities_queryset = Activity.objects.filter(flt).distinct()
    total = activities_queryset.count()
    results = [
        get_search_item(activity, language)
        for activity in activities_queryset[offset : offset + limit]
    ]

    return {
        'label': label_results_generic.get(language),
        'total': total,
        'data': results,
    }


def filter_daterange(values, limit, offset, language):
    if not values:
        raise ParseError('Date range filter needs at least one value', 400)

    flt = None
    for value in values:
        if (
            type(value) is not dict
            or not value.get('date_from')
            or not value.get('date_to')
        ):
            raise ParseError(
                'Date range filter values have to be objects containing from and to properties',
                400,
            )
        d_pattern = r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$'
        d_from = value['date_from']
        d_to = value['date_to']
        if not re.match(d_pattern, d_from) or not re.match(d_pattern, d_to):
            raise ParseError(
                'Only dates of format YYYY-MM-DD can be used as date range filter from and to values',
                400,
            )
        add_flt = (
            Q(activitysearchdates__date__range=[d_from, d_to])
            | Q(activitysearchdateranges__date_from__range=[d_from, d_to])
            | Q(activitysearchdateranges__date_to__range=[d_from, d_to])
        )
        if not flt:
            flt = add_flt
        else:
            flt = flt | add_flt

    activities_queryset = Activity.objects.filter(flt).distinct()
    total = activities_queryset.count()
    results = [
        get_search_item(activity, language)
        for activity in activities_queryset[offset : offset + limit]
    ]

    return {
        'label': label_results_generic.get(language),
        'total': total,
        'data': results,
    }


def filter_type(values, limit, offset, language):
    """Filters all showroom activities for certain types.

    Filters all showroom activities for activities of certain types, that are
    provided through the values parameter. Different values for types are combined
    in a logical OR filter. So all activities will be returned that are of any of
    the provided types.
    The results are paginated by limit and offset values, but a total count for all
    found entities and activities will always be returned in the result.

    :param values: A list of filter id dicts listed by the GET /filters endpoint
    :param limit: Maximum amount of activities to return
    :param offset: The 0-indexed offset of the first activity in the result set
    :return: A SearchResult dictionary, as defined in the API spec.
    """
    if not values:
        raise ParseError('Type filter needs at least one value', 400)

    queryset = Activity.objects.all()
    # TODO: discuss what the ordering criteria are
    queryset = queryset.order_by('-date_created')
    q_filter = None
    for value in values:
        if type(value) is not dict:
            raise ParseError('Malformed type filter', 400)
        if not (typ := value.get('id')):
            raise ParseError('Malformed type filter', 400)
        if type(typ) is not str:
            raise ParseError('Malformed type filter', 400)
        if not q_filter:
            q_filter = Q(type__label__contains={'en': typ})
        else:
            q_filter = q_filter | Q(type__label__contains={'en': typ})
    queryset = queryset.filter(q_filter)

    total_count = queryset.count()

    end = offset + limit
    queryset = queryset[offset:end]

    return {
        'label': 'Activities filtered by type',
        'total': total_count,
        'data': [get_search_item(activity, language) for activity in queryset],
    }


def filter_keywords(values, limit, offset, language):
    """Filters all showroom activities for certain types.

    Filters all showroom activities for activities with certain keywords, that are
    provided through the values parameter. Different values for keywords are combined
    in a logical OR filter. So all activities will be returned that have any of
    the provided keywords.
    The results are paginated by limit and offset values, but a total count for all
    found entities and activities will always be returned in the result.

    :param values: A list of filter id dicts listed by the GET /filters endpoint
    :param limit: Maximum amount of activities to return
    :param offset: The 0-indexed offset of the first activity in the result set
    :return: A SearchResult dictionary, as defined in the API spec.
    """
    if not values:
        raise ParseError('Keywords filter needs at least one value', 400)

    queryset = Activity.objects.all()
    # TODO: discuss what the ordering criteria are
    queryset = queryset.order_by('-date_created')
    for idx, value in enumerate(values):
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

    total_count = queryset.count()

    end = offset + limit
    queryset = queryset[offset:end]

    return {
        'label': 'Activities filtered by keywords',
        'total': total_count,
        'data': [get_search_item(activity, language) for activity in queryset],
    }
