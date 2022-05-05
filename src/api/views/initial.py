import logging
import re

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status, viewsets
from rest_framework.response import Response

from django.utils.text import slugify

from api.serializers.generic import Responses
from api.serializers.initial import InitialDataSerializer
from api.serializers.showcase import get_serialized_showcase_and_warnings
from api.views.search import get_search_results, label_current_activities
from core.models import ShowroomObject
from showroom import settings

logger = logging.getLogger(__name__)


class InitialViewSet(viewsets.GenericViewSet):
    """Initial Landing Page request, delivering "search results" and carousel
    data."""

    serializer_class = InitialDataSerializer

    @extend_schema(
        tags=['public'],
        parameters=[
            OpenApiParameter(
                'limit',
                OpenApiTypes.INT,
                OpenApiParameter.QUERY,
                description=f'Optional limit for the search result. Default: {settings.SEARCH_LIMIT}',
            ),
        ],
        responses={
            200: OpenApiResponse(
                description='',
                response=InitialDataSerializer,
            ),
            404: Responses.Error404,
        },
    )
    def list(self, request, *args, **kwargs):
        if settings.DEFAULT_ENTITY is None:
            return Response(
                {'detail': 'No default entity configured.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return get_initial_response(request, settings.DEFAULT_ENTITY)

    @extend_schema(
        tags=['public'],
        parameters=[
            OpenApiParameter(
                'id',
                OpenApiTypes.STR,
                OpenApiParameter.PATH,
                description='ShortUUID of the entity for which initial data should be presented',
            ),
            OpenApiParameter(
                'limit',
                OpenApiTypes.INT,
                OpenApiParameter.QUERY,
                description=f'Optional limit for the search result. Default: {settings.SEARCH_LIMIT}',
            ),
        ],
        responses={
            200: OpenApiResponse(
                description='',
                response=InitialDataSerializer,
            ),
            404: Responses.Error404,
        },
    )
    def retrieve(self, request, *args, **kwargs):
        pk = kwargs['pk'].split('-')[-1]
        return get_initial_response(request, pk=pk)


def get_initial_response(request, pk):
    try:
        entity = ShowroomObject.active_objects.get(pk=pk)
    except ShowroomObject.DoesNotExist:
        return Response(
            {'detail': 'No entity found with this id.'},
            status=status.HTTP_404_NOT_FOUND,
        )
    lang = request.LANGUAGE_CODE

    limit = request.GET.get('limit')
    if limit is None:
        limit = settings.SEARCH_LIMIT
    else:
        if not re.match(r'^[1-9][0-9]*$', limit):
            return Response(
                {'detail': 'only positive integers are allowed as limit'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        limit = int(limit)

    response = {
        'id': f'{slugify(entity.title)}-{entity.id}',
        'source_institution': {
            'label': entity.source_repo.label_institution,
            'url': entity.source_repo.url_institution,
            'icon': entity.source_repo.icon,
        },
        'showcase': [],
        'results': [],
    }

    if entity.entitydetail.showcase is None or entity.entitydetail.showcase == []:
        entity.entitydetail.showcase = settings.DEFAULT_SHOWCASE

    response['showcase'], showcase_warnings = get_serialized_showcase_and_warnings(
        entity.entitydetail.showcase
    )

    # if anything went wrong with serializing single showcase items, we still want
    # to produce the rest of the showcase, but add warnings too
    if showcase_warnings:
        response['showcase_warnings'] = showcase_warnings

    qs = ShowroomObject.active_objects.filter(
        source_repo__id=settings.DEFAULT_USER_REPO,
        type=ShowroomObject.ACTIVITY,
    )
    count = qs.count()
    results = get_search_results(qs, [], limit, 0, 'currentness', lang)
    response['results'].append(
        {
            'label': label_current_activities[lang],
            'total': count,
            'data': results['data'],
            'search': {
                'order_by': 'currentness',
                'filters': [
                    {
                        'id': 'institution',
                        'filter_values': [
                            {'id': settings.DEFAULT_USER_REPO},
                        ],
                    },
                    {
                        'id': 'showroom_type',
                        'filter_values': [
                            {'id': ShowroomObject.ACTIVITY},
                        ],
                    },
                ],
            },
        }
    )

    return Response(response, status=200)
