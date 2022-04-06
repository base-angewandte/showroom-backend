from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import viewsets
from rest_framework.authentication import BasicAuthentication
from rest_framework.response import Response

from django.conf import settings
from django.db.models import Q

from api.repositories.portfolio.search import get_search_item
from api.serializers.generic import Responses
from api.serializers.search import SearchResultSerializer
from api.serializers.showcase_search import ShowcaseSearchSerializer
from api.views.search import CsrfExemptSessionAuthentication, label_results_generic
from core.models import ShowroomObject


class ShowcaseSearchViewSet(viewsets.GenericViewSet):
    """Submit a specific search for items used in showcase editing."""

    serializer_class = ShowcaseSearchSerializer
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    @extend_schema(
        tags=['public'],
        responses={
            200: OpenApiResponse(
                description='A result set structurally similar to general search results',
                response=SearchResultSerializer,
            ),
            400: Responses.Error400,
        },
    )
    def create(self, request, *args, **kwargs):
        s = self.get_serializer(data=request.data)
        s.is_valid(raise_exception=True)
        q = s.validated_data.get('q')
        sort = s.validated_data.get('sort')
        limit = s.validated_data.get('limit')
        offset = s.validated_data.get('offset')
        exclude = s.validated_data.get('exclude')
        entity_id = s.validated_data.get('entity_id')
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

        if sort is None:
            sort = 'title'
        if exclude is None:
            exclude = []

        entity = None
        if entity_id is not None:
            try:
                entity = ShowroomObject.objects.get(pk=entity_id)
            except ShowroomObject.DoesNotExist:
                return Response({'detail': 'entity_id is not valid'}, status=400)
            if entity.type not in [ShowroomObject.PERSON, ShowroomObject.INSTITUTION]:
                return Response({'detail': 'entity is not of valid type'}, status=400)

        queryset = ShowroomObject.objects.filter(type=ShowroomObject.ACTIVITY)
        if entity:
            if entity.type == ShowroomObject.PERSON:
                queryset = queryset.filter(belongs_to=entity)
            elif entity.type == ShowroomObject.INSTITUTION:
                queryset = queryset.filter(source_repo=entity.source_repo)
        if exclude:
            queryset = queryset.exclude(id__in=exclude)

        q_filter = (
            Q(title__icontains=q)
            | Q(subtext__icontains=q)
            | (
                Q(textsearchindex__text__icontains=q)
                & Q(textsearchindex__language=lang)
            )
        )
        queryset = queryset.filter(q_filter).distinct().order_by(sort)

        count = queryset.count()
        queryset = queryset[offset : limit + offset]

        return Response(
            {
                'label': label_results_generic[lang],
                'total': count,
                'data': [get_search_item(obj, lang) for obj in queryset],
            },
            200,
        )
