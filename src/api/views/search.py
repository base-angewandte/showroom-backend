import logging
import re
from datetime import date, timedelta

from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import mixins, viewsets
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.exceptions import ParseError
from rest_framework.response import Response

from django.conf import settings
from django.contrib.postgres.search import (
    SearchQuery,
    SearchRank,
    SearchVector,
    TrigramSimilarity,
)
from django.db.models import Case, DurationField, F, Min, Q, Sum, Value, When
from django.utils import timezone

from api.repositories.portfolio.search import get_search_item
from api.serializers.generic import Responses
from api.serializers.search import SearchRequestSerializer, SearchResultSerializer
from core.models import ShowroomObject
from general.postgres import SearchVectorJSON

logger = logging.getLogger(__name__)

label_results_generic = {
    'en': 'Search results',
    'de': 'Suchergebnisse',
}
label_current_activities = {
    'en': 'Current activities',
    'de': 'Aktuelle Aktivitäten',
}

text_search_vectors = (
    SearchVector('title', weight='A')
    + SearchVectorJSON('subtext', weight='B')
    + SearchVector('textsearchindex__text_vector', weight='C')
)


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening


class CsrfExemptSessionScheme(OpenApiAuthenticationExtension):
    target_class = CsrfExemptSessionAuthentication
    name = 'cookieAuth'
    priority = -1

    def get_security_definition(self, auto_schema):
        return {
            'type': 'apiKey',
            'in': 'cookie',
            'name': settings.SESSION_COOKIE_NAME,
        }


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
        filters = s.validated_data.get('filters')
        limit = s.validated_data.get('limit')
        offset = s.validated_data.get('offset')
        order_by = s.validated_data.get('order_by')
        lang = request.LANGUAGE_CODE

        queryset = ShowroomObject.active_objects.all()

        return Response(
            get_search_results(queryset, filters, limit, offset, order_by, lang),
            status=200,
        )


def get_search_results(base_queryset, filters, limit, offset, order_by, lang):
    if offset is None:
        offset = 0
    elif offset < 0:
        raise ParseError('negative offset not allowed', 400)
    if limit is not None and limit < 1:
        raise ParseError('negative or zero limit not allowed', 400)
    if limit is None:
        limit = settings.SEARCH_LIMIT
    if order_by is None:
        order_by = 'rank'

    queryset = base_queryset
    q_filter = None
    for flt in filters:
        filter_function_map = {
            'fulltext': get_fulltext_filter,
            'activity': get_activity_filter,
            'person': get_person_filter,
            'date': get_date_filter,
            'daterange': get_daterange_filter,
            'keyword': get_keyword_filter,
            'activity_type': get_activity_type_filter,
            'showroom_type': get_showroom_type_filter,
            'institution': get_institution_filter,
        }
        filter_func = filter_function_map.get(flt['id'])
        if filter_func is None:
            raise ParseError(f'filter id {flt["id"]} is not implemented', 400)
        append_filter = filter_func(flt['filter_values'], lang)
        # if a filter function does not return any filter, we ignore this but log
        # a warning
        if append_filter is None:
            logger.warning(
                f'no filter was returned for {flt["id"]} filter with values: {flt["filter_values"]}'
            )
            continue
        if q_filter is None:
            q_filter = append_filter
        else:
            q_filter = q_filter & append_filter

    if q_filter:
        queryset = queryset.filter(q_filter).distinct()

    if order_by:
        if order_by in ['title', '-title', 'date_changed', '-date_changed']:
            queryset = queryset.order_by(order_by)
        elif order_by == 'currentness':
            now = timezone.now().date()
            zero = timedelta(days=0)
            queryset = (
                queryset.annotate(
                    date_timediff=Min(F('daterelevanceindex__date') - now)
                )
                .annotate(
                    ranked_date_timediff=Case(
                        When(date_timediff__gte=zero, then=F('date_timediff')),
                        When(
                            date_timediff__lt=zero,
                            then=F('date_timediff') * -settings.CURRENTNESS_PAST_WEIGHT,
                        ),
                        output_field=DurationField(),
                    )
                )
                .order_by('ranked_date_timediff')
            )
        elif order_by == 'rank':
            words = []
            for flt in filters:
                if flt['id'] in ['fulltext', 'activity', 'person']:
                    for value in flt['filter_values']:
                        if type(value) == str:
                            words.append(value)
            if words:
                query = ' '.join(words)
                trigram_similarity_title = TrigramSimilarity('title', query)
                trigram_similarity_index = TrigramSimilarity(
                    'textsearchindex__text', query
                )
                rank = trigram_similarity_title + trigram_similarity_index
                queryset = queryset.annotate(rank=rank).order_by('-rank')

    count = queryset.count()
    results = [get_search_item(obj, lang) for obj in queryset[offset : limit + offset]]

    return {
        'label': label_results_generic[lang],
        'total': count,
        'data': results,
    }


def get_fulltext_filter(values, lang):
    filters = None
    for value in values:
        if type(value) is not str:
            raise ParseError('fulltext filter values have to be strings', 400)
        add_filter = (
            Q(title__icontains=value)
            | Q(subtext__icontains=value)
            | (
                Q(textsearchindex__text__icontains=value)
                & Q(textsearchindex__language=lang)
            )
        )
        if filters is None:
            filters = add_filter
        else:
            filters = filters | add_filter
    return filters


def get_activity_filter(values, lang):
    filters = None
    for value in values:
        if type(value) not in [str, dict]:
            raise ParseError(
                'Only strings or dicts are allowed as activity filter parameters', 400
            )
        if type(value) is str:
            add_filter = Q(type=ShowroomObject.ACTIVITY) & (
                Q(title__icontains=value)
                | Q(subtext__icontains=value)
                | (
                    Q(textsearchindex__text__icontains=value)
                    & Q(textsearchindex__language=lang)
                )
            )
        else:
            obj_id = value.get('id')
            if not obj_id or type(obj_id) is not str:
                raise ParseError(
                    'dict values in activity filter have to contain an id of type str',
                    400,
                )
            add_filter = Q(pk=obj_id) | Q(relations_to__id=obj_id)
        if filters is None:
            filters = add_filter
        else:
            filters = filters | add_filter
    return filters


def get_person_filter(values, lang):
    filters = None
    for value in values:
        if type(value) not in [str, dict]:
            raise ParseError(
                'Only strings or dicts are allowed as person filter parameters', 400
            )
        if type(value) is str:
            add_filter = Q(
                type__in=[
                    ShowroomObject.PERSON,
                    ShowroomObject.DEPARTMENT,
                    ShowroomObject.INSTITUTION,
                ]
            ) & (
                Q(title__icontains=value)
                | Q(subtext__icontains=value)
                | (
                    Q(textsearchindex__text__icontains=value)
                    & Q(textsearchindex__language=lang)
                )
            )
        else:
            obj_id = value.get('id')
            if not obj_id or type(obj_id) is not str:
                raise ParseError(
                    'dict values in person filter have to contain an id of type str',
                    400,
                )
            obj_id = obj_id.split('-')[-1]
            add_filter = Q(pk=obj_id) | Q(relations_to__id=obj_id)
        if filters is None:
            filters = add_filter
        else:
            filters = filters | add_filter
    return filters


def get_date_filter(values, lang):
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
        add_flt = Q(datesearchindex__date=value) | (
            Q(daterangesearchindex__date_from__lte=value)
            & Q(daterangesearchindex__date_to__gte=value)
        )
        if not flt:
            flt = add_flt
        else:
            flt = flt | add_flt
    return flt


def get_daterange_filter(values, lang):
    if not values:
        raise ParseError('Date range filter needs at least one value', 400)

    flt = None
    for value in values:
        if type(value) is not dict or (
            value.get('date_from') is None and value.get('date_to') is None
        ):
            raise ParseError(
                'Date range filter values have to be objects containing date_from and date_to properties',
                400,
            )

        d_pattern = r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$'
        d_from = value.get('date_from')
        d_to = value.get('date_to')
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
                Q(datesearchindex__date__gte=d_from)
                | Q(daterangesearchindex__date_from__gte=d_from)
                | Q(daterangesearchindex__date_to__gte=d_from)
            )
        # in case only date_to is provided, all dates past this date should be found
        elif not d_from:
            add_flt = (
                Q(datesearchindex__date__lte=d_to)
                | Q(daterangesearchindex__date_from__lte=d_to)
                | Q(daterangesearchindex__date_to__lte=d_to)
            )
        # if both parameters are provided, we search within the given date range
        else:
            add_flt = (
                Q(datesearchindex__date__range=[d_from, d_to])
                | Q(daterangesearchindex__date_from__range=[d_from, d_to])
                | Q(daterangesearchindex__date_to__range=[d_from, d_to])
            )
        if not flt:
            flt = add_flt
        else:
            flt = flt | add_flt

    return flt


def get_keyword_filter(values, lang):
    if not values:
        raise ParseError('Keywords filter needs at least one value', 400)

    flt = None
    for value in values:
        if type(value) is not dict:
            raise ParseError('Malformed keyword filter', 400)
        if not (kw := value.get('id')):
            raise ParseError('Malformed keyword filter', 400)
        if type(kw) is not str:
            raise ParseError('Malformed keyword filter', 400)
        if flt is None:
            flt = Q(activitydetail__keywords__has_key=kw)
        else:
            flt = flt | Q(activitydetail__keywords__has_key=kw)
    return Q(type=ShowroomObject.ACTIVITY) & flt


def get_activity_type_filter(values, lang):
    if not values:
        raise ParseError('Type filter needs at least one value', 400)

    flt = None
    for value in values:
        if type(value) is not dict:
            raise ParseError('Malformed type filter', 400)
        if not (typ := value.get('id')):
            raise ParseError('Malformed type filter', 400)
        if type(typ) is not str:
            raise ParseError('Malformed type filter', 400)
        if not flt:
            flt = Q(activitydetail__activity_type__label__contains={'en': typ})
        else:
            flt = flt | Q(activitydetail__activity_type__label__contains={'en': typ})
    return Q(type=ShowroomObject.ACTIVITY) & flt


def get_showroom_type_filter(values, lang):
    if not values:
        raise ParseError('Type filter needs at least one value', 400)

    flt = None
    for value in values:
        if type(value) is not dict:
            raise ParseError('Malformed type filter', 400)
        if not (typ := value.get('id')):
            raise ParseError('Malformed type filter', 400)
        if type(typ) is not str:
            raise ParseError('Malformed type filter', 400)
        if typ not in [ShowroomObject.ACTIVITY, ShowroomObject.PERSON]:
            raise ParseError('Invalid showroom type', 400)
        if not flt:
            flt = Q(type=typ)
        else:
            flt = flt | Q(type=typ)
    return flt


def get_institution_filter(values, lang):
    if not values:
        raise ParseError('institution filter needs at least one value', 400)

    flt = None
    for value in values:
        if type(value) is not dict:
            raise ParseError('Malformed institution filter', 400)
        if not (repo_id := value.get('id')):
            raise ParseError('Malformed institution filter', 400)
        if type(repo_id) is not int:
            raise ParseError('Malformed institution filter', 400)
        if not flt:
            flt = Q(source_repo__id=repo_id)
        else:
            flt = flt | Q(source_repo__id=repo_id)
    return flt


# TODO: once the new search is fully implemented, throw out dead code below


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

    vector = SearchVector('textsearchindex__text_vector')
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
        ShowroomObject.active_objects.filter(textsearchindex__language=language)
        .annotate(rank=rank)
        .exclude(rank=0)
        .distinct()
        .order_by('-rank')
    )
    found_activities_count = activities_queryset.count()
    # TODO: adapt to new model and use standard text search with trigram similarity

    # Before we apply any pagination, we also search through all related entities, to
    # get their total count as well.
    vector = SearchVector('showroomobject__textsearchindex__text_vector')
    rank = SearchRank(vector, query, cover_density=True, normalization=Value(2))
    entities_queryset = (
        ShowroomObject.active_objects.filter(
            showroomobject__textsearchindex__language=language
        )
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

    activities_queryset = ShowroomObject.active_objects.filter(
        type=ShowroomObject.ACTIVITY
    )
    today = date.today()
    future_limit = today + timedelta(days=settings.CURRENT_ACTIVITIES_FUTURE)
    past_limit = today - timedelta(days=settings.CURRENT_ACTIVITIES_PAST)

    today_activities = activities_queryset.filter(datesearchindex__date=today)
    today_count = today_activities.count()
    future_activities = (
        activities_queryset.filter(
            (
                Q(datesearchindex__date__gt=today)
                & Q(datesearchindex__date__lte=future_limit)
            )
            | (
                Q(daterangesearchindex__date_to__gt=today)
                & Q(daterangesearchindex__date_to__lte=future_limit)
            )
            | (
                Q(daterangesearchindex__date_from__gt=today)
                & Q(daterangesearchindex__date_from__lte=future_limit)
            )
        )
        # exclude entries that are already in today_activities
        .exclude(datesearchindex__date=today)
        # filter out duplicates
        .distinct()
    )
    future_count = future_activities.count()
    past_activities = (
        activities_queryset.filter(
            (
                Q(datesearchindex__date__lt=today)
                & Q(datesearchindex__date__gte=past_limit)
            )
            | (
                Q(daterangesearchindex__date_from__lt=today)
                & Q(daterangesearchindex__date_from__gte=past_limit)
            )
            | (
                Q(daterangesearchindex__date_to__lt=today)
                & Q(daterangesearchindex__date_to__gte=past_limit)
            )
        )
        # exclude entries that are already in today_activities
        .exclude(datesearchindex__date=today)
        # exclude entries that are already in future_activities
        .exclude(
            (
                Q(datesearchindex__date__gt=today)
                & Q(datesearchindex__date__lte=future_limit)
            )
            | (
                Q(daterangesearchindex__date_to__gt=today)
                & Q(daterangesearchindex__date_to__lte=future_limit)
            )
            | (
                Q(daterangesearchindex__date_from__gt=today)
                & Q(daterangesearchindex__date_from__lte=future_limit)
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
