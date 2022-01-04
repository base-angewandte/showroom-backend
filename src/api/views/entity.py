from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from api.serializers.entity import EntitySerializer
from api.serializers.generic import Responses
from api.serializers.search import SearchRequestSerializer, SearchResultSerializer
from core.models import Entity


@extend_schema_view(
    create=extend_schema(
        tags=['repo'],
        responses={
            201: EntitySerializer,
            400: Responses.Error400,
            403: Responses.Error403,
        },
    ),
    retrieve=extend_schema(
        tags=['public'],
        responses={
            200: EntitySerializer,
            404: Responses.Error404,
        },
    ),
    partial_update=extend_schema(
        tags=['auth'],
        responses={
            204: None,
            400: Responses.Error400,
            403: Responses.Error403,
            404: Responses.Error404,
        },
    ),
)
class EntityViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Entity.objects.all()
    serializer_class = EntitySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    # we only want partial updates enabled, therefore removing put
    # from the allowed methods
    http_method_names = ['get', 'head', 'options', 'patch', 'post', 'put']

    @extend_schema(exclude=True)
    def list(self, request, *args, **kwargs):
        # If we do not include the ListModelMixin and define this here, Django would
        # provide a standard 404 HTML page. So to be consistent with the APIs error
        # scheme we raise a rest_framework 405, and exclude the list method in the
        # schema (through the list parameter in the extend_schema_view decorator
        # above)
        raise MethodNotAllowed(method='GET')

    @extend_schema(
        tags=['public'],
        responses={
            200: EntitySerializer(),
            404: Responses.Error404,
        },
    )
    def retrieve(self, request, *args, **kwargs):
        pk = kwargs['pk'].split('-')[-1]
        instance = get_object_or_404(self.queryset, pk=pk)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @extend_schema(
        tags=['public'],
        responses={
            200: Responses.CommonList,
            404: Responses.Error404,
        },
    )
    @action(detail=True, methods=['get'], url_path='list')
    def activities_list(self, request, *args, **kwargs):
        pk = kwargs['pk'].split('-')[-1]
        instance = get_object_or_404(self.queryset, pk=pk)
        return Response(instance.list if instance.list else [], status=200)

    @extend_schema(
        tags=['public'],
        responses={
            200: SearchResultSerializer(many=True),
            404: Responses.Error404,
        },
        # TODO: change parameters
    )
    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def search(self, request, *args, **kwargs):
        s = SearchRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(
            {
                'label': 'Entity search is not yet implemented',
                'total': 0,
                'data': [],
            },
            status=200,
        )
