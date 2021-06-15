from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from core.models import Activity, Album, Entity, Media

from . import view_spec
from .permissions import ActivityPermission
from .serializers import (
    ActivitySerializer,
    AlbumSerializer,
    EntitySerializer,
    MediaSerializer,
)

# Create your views here.


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
    list=extend_schema(exclude=True),
    activities_list=extend_schema(
        tags=['public'],
        responses={
            200: view_spec.Responses.CommonList,
            404: view_spec.Responses.Error404,
        },
    ),
    search=extend_schema(
        tags=['public'],
        responses={
            200: view_spec.Responses.SearchCollection,
            404: view_spec.Responses.Error404,
        },
        # TODO: change parameters
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
    # we only want partial updates enabled, therefore removing put from the allowed methods
    http_method_names = ['get', 'head', 'options', 'patch', 'post']

    def list(self, request, *args, **kwargs):
        # If we do not include the ListModelMixin and define this here, Django would provide a standard 404
        # HTML page. So to be consistent with the APIs error scheme we raise a rest_framework 405, and exclude
        # the list method in the schema (through the list parameter in the extend_schema_view decorator above)
        raise MethodNotAllowed(method='GET')

    @action(detail=True, methods=['get'], url_path='list')
    def activities_list(self, request, *args, **kwargs):
        return Response({'detail': 'Not yet implemented'}, status=400)

    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def search(self, request, *args, **kwargs):
        s = view_spec.SearchSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(
            {'detail': 'Not yet implemented', 'filters_used': s.validated_data},
            status=400,
        )


@extend_schema_view(
    create=extend_schema(
        tags=['repo'],
        responses={
            201: ActivitySerializer,
            400: view_spec.Responses.Error400,
            403: view_spec.Responses.Error403,
        },
    ),
    destroy=extend_schema(
        tags=['repo'],
        responses={
            204: None,
            400: view_spec.Responses.Error400,
            403: view_spec.Responses.Error403,
            404: view_spec.Responses.Error404,
        },
    ),
    retrieve=extend_schema(
        tags=['public'],
        responses={
            200: ActivitySerializer,
            404: view_spec.Responses.Error404,
        },
    ),
    media=extend_schema(
        tags=['public'],
        responses={
            200: MediaSerializer(many=True),
            404: view_spec.Responses.Error404,
        },
    ),
    list=extend_schema(exclude=True),
)
class ActivityViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    permission_classes = [ActivityPermission]

    def list(self, request, *args, **kwargs):
        # Similar to list in EntitiyViewSet
        raise MethodNotAllowed(method='GET')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            instance = Activity.objects.get(
                source_repo_entry_id=serializer.validated_data['source_repo_entry_id'],
                source_repo=serializer.validated_data['source_repo'],
            )
            serializer.instance = instance
        except Activity.DoesNotExist:
            instance = False
        except Activity.MultipleObjectsReturned:
            return Response(
                {
                    'detail': 'More than one activity with this id exists. This should not happen. Contact the showroom admin.'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        serializer.save()

        response = {
            'created': [],
            'updated': [],
            'errors': [],
        }
        if instance:
            response['updated'].append(
                {
                    'id': serializer.validated_data['source_repo_entry_id'],
                    'showroom_id': serializer.data['id'],
                }
            )
        else:
            response['created'].append(
                {
                    'id': serializer.validated_data['source_repo_entry_id'],
                    'showroom_id': serializer.data['id'],
                }
            )

        return Response(response, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def media(self, request, *args, **kwargs):
        return Response({'detail': 'Not yet implemented'}, status=400)


@extend_schema_view(
    create=extend_schema(
        tags=['auth'],
        responses={
            201: AlbumSerializer,
            400: view_spec.Responses.Error400,
            403: view_spec.Responses.Error403,
        },
    ),
    partial_update=extend_schema(
        tags=['auth'],
        responses={
            200: AlbumSerializer,
            400: view_spec.Responses.Error400,
            403: view_spec.Responses.Error403,
            404: view_spec.Responses.Error404,
        },
    ),
    destroy=extend_schema(
        tags=['auth'],
        responses={
            204: None,
            400: view_spec.Responses.Error400,
            403: view_spec.Responses.Error403,
            404: view_spec.Responses.Error404,
        },
    ),
    retrieve=extend_schema(
        tags=['public'],
        responses={
            200: AlbumSerializer,
            404: view_spec.Responses.Error404,
        },
    ),
    update=extend_schema(exclude=True),
    list=extend_schema(exclude=True),
)
class AlbumViewSet(viewsets.ModelViewSet):
    queryset = Album.objects.all()
    serializer_class = AlbumSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def list(self, request, *args, **kwargs):
        # Similar to list in EntitiyViewSet
        raise MethodNotAllowed(method='GET')


@extend_schema_view(
    create=extend_schema(
        tags=['repo'],
        responses={
            201: MediaSerializer,
            400: view_spec.Responses.Error400,
            403: view_spec.Responses.Error403,
            404: view_spec.Responses.Error404,
        },
    ),
    update=extend_schema(
        tags=['repo'],
        responses={
            200: MediaSerializer,
            400: view_spec.Responses.Error400,
            403: view_spec.Responses.Error403,
            404: view_spec.Responses.Error404,
        },
    ),
    destroy=extend_schema(
        tags=['repo'],
        responses={
            204: None,
            400: view_spec.Responses.Error400,
            403: view_spec.Responses.Error403,
            404: view_spec.Responses.Error404,
        },
    ),
    partial_update=extend_schema(exclude=True),
)
class MediaViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Media.objects.all()
    serializer_class = MediaSerializer


@extend_schema_view(
    create=extend_schema(
        tags=['public'],
        responses={
            200: view_spec.Responses.SearchCollection,
            400: view_spec.Responses.Error400,
        },
    )
)
class SearchViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Submit a search to Showroom."""

    serializer_class = view_spec.SearchSerializer

    def create(self, request, *args, **kwargs):
        s = view_spec.SearchSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(
            {'detail': 'Not yet implemented', 'filters_used': s.validated_data},
            status=400,
        )


@extend_schema_view(
    list=extend_schema(
        tags=['public'],
        responses={
            200: view_spec.Responses.Filters,
        },
    )
)
class FilterViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Get all the available filters that can be used in search and
    autocomplete."""

    def list(self, request, *args, **kwargs):
        return Response({'detail': 'Not yet implemented'}, status=400)


@extend_schema_view(
    create=extend_schema(
        tags=['public'],
        responses={
            200: view_spec.Responses.AutoComplete,
        },
    )
)
class AutocompleteViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Retrieves available autocomplete results for a specific string and
    filter."""

    def create(self, request, *args, **kwargs):
        return Response({'detail': 'Not yet implemented'}, status=400)
