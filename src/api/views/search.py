import re
from datetime import date, timedelta

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import mixins, viewsets
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.exceptions import ParseError
from rest_framework.response import Response

from django.conf import settings
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db.models import Q, Sum, Value

from api.repositories.portfolio.search import get_search_item
from api.serializers.generic import Responses
from api.serializers.search import SearchRequestSerializer, SearchResultSerializer
from core.models import ShowroomObject

label_results_generic = {
    'en': 'Search results',
    'de': 'Suchergebnisse',
}
label_current_activities = {
    'en': 'Current activities',
    'de': 'Aktuelle Aktivitäten',
}


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening


class SearchViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Submit a search to Showroom."""

    serializer_class = SearchRequestSerializer
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    @extend_schema(
        tags=['public'],
        responses={
            200: OpenApiResponse(
                description='',
                response=SearchResultSerializer,
            ),
            400: Responses.Error400,
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


def text_search_query(text):
    words = re.findall(r'[\w]+', text)
    if not words:
        raise ParseError(
            f'The value "{text}" does not contain any valid search words',
            400,
        )
    query = None
    for word in words:
        if query is None:
            query = SearchQuery(word + ':*', config='simple', search_type='raw')
        else:
            query = query | SearchQuery(word + ':*', config='simple', search_type='raw')
    return query


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
    if not values:
        raise ParseError('Activities filter needs at least one value', 400)

    vector = SearchVector('activitysearch__text_vector')
    query = None
    for _idx, value in enumerate(values):
        if type(value) is not str:
            raise ParseError(
                'Only strings are allowed for activities/persons/locations/default filters',
                400,
            )
        if query is None:
            query = text_search_query(value)
        else:
            query = query | text_search_query(value)
    rank = SearchRank(vector, query, cover_density=True, normalization=Value(2))
    activities_queryset = (
        ShowroomObject.objects.filter(textsearchindex__language=language)
        .annotate(rank=rank)
        .exclude(rank=0)
        .distinct()
        .order_by('-rank')
    )
    found_activities_count = activities_queryset.count()
    # TODO: adapt to new model and use standard text search with trigram similarity

    # Before we apply any pagination, we also search through all related entities, to
    # get their total count as well.
    vector = SearchVector('activity__activitysearch__text_vector')
    rank = SearchRank(vector, query, cover_density=True, normalization=Value(2))
    entities_queryset = (
        ShowroomObject.objects.filter(activity__activitysearch__language=language)
        .annotate(rank=Sum(rank))
        .exclude(rank=0)
        .distinct()
        .order_by('-rank')
    )
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

    activities_queryset = ShowroomObject.objects.filter(type=ShowroomObject.ACTIVITY)
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
                Q(activitysearchdateranges__date_to__gt=today)
                & Q(activitysearchdateranges__date_to__lte=future_limit)
            )
            | (
                Q(activitysearchdateranges__date_from__gt=today)
                & Q(activitysearchdateranges__date_from__lte=future_limit)
            )
        )
        # exclude entries that are already in today_activities
        .exclude(activitysearchdates__date=today)
        # filter out duplicates
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
                & Q(activitysearchdateranges__date_from__gte=past_limit)
            )
            | (
                Q(activitysearchdateranges__date_to__lt=today)
                & Q(activitysearchdateranges__date_to__gte=past_limit)
            )
        )
        # exclude entries that are already in today_activities
        .exclude(activitysearchdates__date=today)
        # exclude entries that are already in future_activities
        .exclude(
            (
                Q(activitysearchdates__date__gt=today)
                & Q(activitysearchdates__date__lte=future_limit)
            )
            | (
                Q(activitysearchdateranges__date_to__gt=today)
                & Q(activitysearchdateranges__date_to__lte=future_limit)
            )
            | (
                Q(activitysearchdateranges__date_from__gt=today)
                & Q(activitysearchdateranges__date_from__lte=future_limit)
            )
        )
        # filter out duplicates
        .distinct()
    )
    past_count = past_activities.count()

    # TODO: for now we have three unranked querysets, so we'll just evaluate them
    #       in full, if the requested offset + limit demand it.
    #       this could be made more efficient, but in the end we might want to have
    #       only one queryset with an annotated rank. this should be discussed first.
    if offset + limit <= today_count:
        final = today_activities
    else:
        final = [activity for activity in today_activities]
        final.extend([a for a in future_activities])
        if offset + limit > today_count + future_count:
            final.extend([a for a in past_activities])

    return {
        'label': label_current_activities.get(language),
        'total': today_count + future_count + past_count,
        'data': [
            get_search_item(activity, language)
            for activity in final[offset : offset + limit]
        ],
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

    activities_queryset = ShowroomObject.objects.filter(flt).distinct()
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
            or value.get('date_from') is None
            or value.get('date_to') is None
        ):
            raise ParseError(
                'Date range filter values have to be objects containing date_from and date_to properties',
                400,
            )

        d_pattern = r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$'
        d_from = value['date_from']
        d_to = value['date_to']
        if (d_from and not re.match(d_pattern, d_from)) or (
            d_to and not re.match(d_pattern, d_to)
        ):
            raise ParseError(
                'Only dates of format YYYY-MM-DD can be used as date range filter from and to values',
                400,
            )
        if not d_from and not d_to:
            raise ParseError(
                'At least one of the two date range parameters have to be valid dates',
                400,
            )
        # in case only date_from is provided, all dates in its future should be found
        if not d_to:
            add_flt = (
                Q(activitysearchdates__date__gte=d_from)
                | Q(activitysearchdateranges__date_from__gte=d_from)
                | Q(activitysearchdateranges__date_to__gte=d_from)
            )
        # in case only date_to is provided, all dates past this date should be found
        elif not d_from:
            add_flt = (
                Q(activitysearchdates__date__lte=d_to)
                | Q(activitysearchdateranges__date_from__lte=d_to)
                | Q(activitysearchdateranges__date_to__lte=d_to)
            )
        # if both parameters are provided, we search within the given date range
        else:
            add_flt = (
                Q(activitysearchdates__date__range=[d_from, d_to])
                | Q(activitysearchdateranges__date_from__range=[d_from, d_to])
                | Q(activitysearchdateranges__date_to__range=[d_from, d_to])
            )
        if not flt:
            flt = add_flt
        else:
            flt = flt | add_flt

    activities_queryset = ShowroomObject.objects.filter(flt).distinct()
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

    queryset = ShowroomObject.objects.all()
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

    queryset = ShowroomObject.objects.all()
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
