from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from api import view_spec
from api.serializers.entity import EntitySerializer
from api.serializers.search import SearchCollectionSerializer, SearchRequestSerializer
from core.models import Entity


@extend_schema_view(
    create=extend_schema(
        tags=['repo'],
        responses={
            201: EntitySerializer,
            400: view_spec.Responses.Error400,
            403: view_spec.Responses.Error403,
        },
    ),
    retrieve=extend_schema(
        tags=['public'],
        responses={
            200: EntitySerializer,
            404: view_spec.Responses.Error404,
        },
    ),
    partial_update=extend_schema(
        tags=['auth'],
        responses={
            204: None,
            400: view_spec.Responses.Error400,
            403: view_spec.Responses.Error403,
            404: view_spec.Responses.Error404,
        },
    ),
)
class EntityViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Entity.objects.all()
    serializer_class = EntitySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    # we only want partial updates enabled, therefore removing put
    # from the allowed methods
    http_method_names = ['get', 'head', 'options', 'patch', 'post']

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
            200: view_spec.Responses.CommonList,
            404: view_spec.Responses.Error404,
        },
    )
    @action(detail=True, methods=['get'], url_path='list')
    def activities_list(self, request, *args, **kwargs):
        return Response({'detail': 'Not yet implemented'}, status=400)

    @extend_schema(
        tags=['public'],
        responses={
            200: SearchCollectionSerializer,
            404: view_spec.Responses.Error404,
        },
        # TODO: change parameters
    )
    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def search(self, request, *args, **kwargs):
        s = SearchRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(
            {'detail': 'Not yet implemented', 'filters_used': s.validated_data},
            status=400,
        )
