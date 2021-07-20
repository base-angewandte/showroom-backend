from drf_spectacular.utils import OpenApiExample, extend_schema, inline_serializer
from rest_framework import mixins, serializers, viewsets
from rest_framework.response import Response

from django.conf import settings

search_categories = [
    {'id': 'persons', 'label': {'en': 'Persons', 'de': 'Personen'}},
    {'id': 'activities', 'label': {'en': 'Activities', 'de': 'Aktivitäten'}},
]


def get_localised_search_categories(lang):
    if lang not in [ln[0] for ln in settings.LANGUAGES]:
        lang = settings.LANGUAGES[0][0]
    return [
        {
            'id': cat['id'],
            'label': cat['label'][lang],
        }
        for cat in search_categories
    ]


class CategoryViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Return all possible categories for the search results."""

    @extend_schema(
        tags=['public'],
        responses={
            200: inline_serializer(
                name='Category',
                fields={
                    'id': serializers.CharField(),
                    'label': serializers.CharField(),
                },
            ),
        },
        examples=[
            OpenApiExample(
                name='Error',
                value=search_categories,
                status_codes=['200'],
                response_only=True,
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        lang = request.LANGUAGE_CODE
        return Response(get_localised_search_categories(lang), status=200)
