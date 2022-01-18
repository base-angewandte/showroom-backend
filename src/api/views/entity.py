from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from api.serializers.entity import EntityEditSerializer, EntitySerializer
from api.serializers.generic import Responses
from api.serializers.search import SearchRequestSerializer, SearchResultSerializer
from api.serializers.showcase import ShowcaseSerializer
from api.views.search import CsrfExemptSessionAuthentication
from core.models import Activity, Album, Entity


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
        tags=['auth'],
        parameters=[
            OpenApiParameter(
                name='secondary_details',
                type=bool,
                default=False,
                location=OpenApiParameter.QUERY,
                description='[GET only:] Whether to include secondary_details in the response',
            ),
            OpenApiParameter(
                name='showcase',
                type=bool,
                default=False,
                location=OpenApiParameter.QUERY,
                description='[GET only:] Whether to include showcase in the response',
            ),
        ],
        request=EntityEditSerializer,
        responses={
            200: EntityEditSerializer,
            403: Responses.Error403,
            404: Responses.Error404,
        },
    )
    @action(
        detail=True,
        methods=['get', 'patch'],
        url_path='edit',
        permission_classes=[IsAuthenticated],
        authentication_classes=[CsrfExemptSessionAuthentication],
    )
    def edit(self, request, *args, **kwargs):
        pk = kwargs['pk'].split('-')[-1]
        instance = get_object_or_404(self.queryset, pk=pk)
        # GET /entities/{id}/edit
        if request.method.lower() == 'get':
            # validate query parameters
            include_showcase = False
            include_showcase_details = False
            include_secondary_details = False
            if 'showcase' in request.query_params:
                include_showcase = parse_boolean_query_param(
                    'showcase', request.query_params['showcase']
                )
            if 'showcase_details' in request.query_params:
                include_showcase_details = parse_boolean_query_param(
                    'showcase_details', request.query_params['showcase_details']
                )
            if 'secondary_details' in request.query_params:
                include_secondary_details = parse_boolean_query_param(
                    'secondary_details', request.query_params['secondary_details']
                )
            # now assemble the return dict
            ret = {}
            if include_showcase:
                ret['showcase'] = []
                if instance.showcase:
                    for sc_id, sc_type in instance.showcase:
                        sc_item = {'id': sc_id, 'type': sc_type}
                        if include_showcase_details:
                            sc_item['details'] = {}
                            item = None
                            if sc_type == 'activity':
                                try:
                                    item = Activity.objects.get(pk=sc_id)
                                except Activity.DoesNotExist:
                                    pass
                            elif sc_type == 'album':
                                try:
                                    item = Album.objects.get(pk=sc_id)
                                except Album.DoesNotExist:
                                    pass
                            if item:
                                sc_item['details'] = ShowcaseSerializer(item).data
                        ret['showcase'].append(sc_item)
            if include_secondary_details:
                ret['secondary_details'] = instance.secondary_details

        # PATCH /entities/{id}/edit
        else:
            return Response({'detail': 'PATCH not yet implemented'}, status=200)

        return Response(ret, status=200)

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


def parse_boolean_query_param(key, value):
    if value == 'true':
        return True
    elif value == 'false':
        return False
    else:
        raise serializers.ValidationError(
            {key: 'If used, has to be either true or false.'}
        )
