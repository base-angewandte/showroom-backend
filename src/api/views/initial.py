import logging

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.response import Response

from api import view_spec
from api.serializers.initial import InitialDataSerializer
from api.serializers.showcase import get_serialized_showcase_and_warnings
from api.views.search import filter_activities
from core.models import Entity
from showroom import settings

logger = logging.getLogger(__name__)


class InitialViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Initial Landing Page request, delivering "search results" and carousel
    data."""

    serializer_class = InitialDataSerializer

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
            404: view_spec.Responses.Error404,
        },
    )
    def retrieve(self, request, *args, **kwargs):
        try:
            entity = Entity.objects.get(pk=kwargs['pk'])
        except Entity.DoesNotExist:
            return Response(
                {'detail': 'No entity found with this id.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        lang = request.LANGUAGE_CODE

        response = {
            'id': entity.id,
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
            'id': 'activities',
            'filter_values': ['a'],
        }
        found = filter_activities(filter['filter_values'], 30, 0, lang)
        response['results'].append(
            {
                'label': 'Current activities',
                'total': found['total'],
                'data': found['data'],
                'filters': [filter],
            }
        )

        return Response(response, status=200)