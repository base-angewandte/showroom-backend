from drf_spectacular.utils import OpenApiExample, extend_schema, inline_serializer
from rest_framework import mixins, serializers, viewsets
from rest_framework.response import Response

search_categories = [
    {'id': 'persons', 'label': 'Persons'},
    {'id': 'activities', 'label': 'Activities'},
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
        print(lang)
        return Response(search_categories, status=200)
