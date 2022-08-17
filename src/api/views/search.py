import logging
import re
from datetime import timedelta

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
from django.db.models import Case, DurationField, F, Min, Q, When
from django.utils import timezone

from api.repositories.portfolio.search import get_search_item
from api.repositories.portfolio.utils import get_usernames_from_roles
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

                # TODO exchanged trigram with search vector
                # trigram_similarity_index = TrigramSimilarity(
                #     'textsearchindex__text', query
                # )
                # rank = trigram_similarity_title + trigram_similarity_index
                search_query = SearchQuery(query)
                search_rank = SearchRank(text_search_vectors, search_query)
                rank = trigram_similarity_title + search_rank

                queryset = queryset.annotate(rank=rank).order_by('-rank')
            else:
                queryset.order_by()

    count = queryset.count()
    queryset = queryset.select_related()[offset : limit + offset]
    results = [get_search_item(obj, lang) for obj in queryset]

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
            try:
                activity = ShowroomObject.active_objects.get(pk=obj_id)
            except ShowroomObject.DoesNotExist as err:
                raise ParseError('requested activity does not exist', 400) from err
            contributor_ids = get_usernames_from_roles(activity)
            add_filter = (
                Q(pk=obj_id)
                | Q(relations_to__id=obj_id)
                | Q(
                    type=ShowroomObject.PERSON,
                    source_repo_object_id__in=contributor_ids,
                )
            )
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
            try:
                person = ShowroomObject.active_objects.get(pk=obj_id)
            except ShowroomObject.DoesNotExist as err:
                raise ParseError('requested person does not exist', 400) from err
            add_filter = Q(pk=obj_id) | Q(
                related_usernames__contributor_source_id=person.source_repo_object_id
            )
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
                | Q(
                    daterangesearchindex__date_from__lte=d_from,
                    daterangesearchindex__date_to__gte=d_to,
                )
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
