import logging

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status, viewsets
from rest_framework.response import Response

from django.utils.text import slugify

from api.serializers.generic import Responses
from api.serializers.initial import InitialDataSerializer
from api.serializers.showcase import get_serialized_showcase_and_warnings
from api.views.search import filter_current_activities
from core.models import Entity
from showroom import settings

logger = logging.getLogger(__name__)


class InitialViewSet(viewsets.GenericViewSet):
    """Initial Landing Page request, delivering "search results" and carousel
    data."""

    serializer_class = InitialDataSerializer

    @extend_schema(
        tags=['public'],
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
        entity = Entity.objects.get(pk=pk)
    except Entity.DoesNotExist:
        return Response(
            {'detail': 'No entity found with this id.'},
            status=status.HTTP_404_NOT_FOUND,
        )
    lang = request.LANGUAGE_CODE

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

    if entity.showcase is None or entity.showcase == []:
        entity.showcase = settings.DEFAULT_SHOWCASE

    response['showcase'], showcase_warnings = get_serialized_showcase_and_warnings(
        entity.showcase
    )

    # if anything went wrong with serializing single showcase items, we still want
    # to produce the rest of the showcase, but add warnings too
    if showcase_warnings:
        response['showcase_warnings'] = showcase_warnings

    filter = {
        'id': 'current_activities',
        'filter_values': ['42!'],  # TODO: placeholder value until further discussion
    }
    found = filter_current_activities(filter['filter_values'], 30, 0, lang)
    response['results'].append(
        {
            'label': found['label'],
            'total': found['total'],
            'data': found['data'],
            'filters': [filter],
        }
    )

    return Response(response, status=200)
