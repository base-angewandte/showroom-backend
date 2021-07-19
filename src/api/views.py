from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from core.models import Activity, Album, Entity, Media

from . import view_spec
from .permissions import ActivityPermission
from .serializers.activity import ActivitySerializer
from .serializers.album import AlbumSerializer
from .serializers.entity import EntitySerializer
from .serializers.media import MediaSerializer

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
            200: view_spec.Responses.SearchCollection,
            404: view_spec.Responses.Error404,
        },
        # TODO: change parameters
    )
    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def search(self, request, *args, **kwargs):
        s = view_spec.SearchSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(
            {'detail': 'Not yet implemented', 'filters_used': s.validated_data},
            status=400,
        )


@extend_schema_view(
    retrieve=extend_schema(
        tags=['public'],
        responses={
            200: ActivitySerializer,
            404: view_spec.Responses.Error404,
        },
    ),
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

    @extend_schema(exclude=True)
    def list(self, request, *args, **kwargs):
        # Similar to list in EntitiyViewSet
        raise MethodNotAllowed(method='GET')

    @extend_schema(
        tags=['repo'],
        responses={
            201: ActivitySerializer,
            400: view_spec.Responses.Error400,
            403: view_spec.Responses.Error403,
        },
    )
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
                    'detail': 'More than one activity with this id exists. '
                    + 'This should not happen. Contact the showroom admin.'
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

    @extend_schema(
        tags=['repo'],
        parameters=[
            OpenApiParameter(
                name='id',
                type=str,
                location=OpenApiParameter.PATH,
                description='The source repo\'s id for this activity',
            ),
        ],
        responses={
            204: None,
            400: view_spec.Responses.Error400,
            403: view_spec.Responses.Error403,
            404: view_spec.Responses.Error404,
        },
    )
    def destroy(self, request, *args, **kwargs):
        try:
            activity = Activity.objects.get(
                source_repo_entry_id=kwargs['pk'],
                source_repo_id=request.META.get('HTTP_X_API_CLIENT'),
            )
        except Activity.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        self.perform_destroy(activity)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        tags=['public'],
        responses={
            200: MediaSerializer(many=True),
            404: view_spec.Responses.Error404,
        },
    )
    @action(detail=True, methods=['get'])
    def media(self, request, *args, **kwargs):
        return Response({'detail': 'Not yet implemented'}, status=400)

    @extend_schema(
        tags=['repo'],
        request=view_spec.ActivityRelationSerializer,
        responses={
            201: view_spec.Responses.RelationAdded,
            400: view_spec.Responses.Error400,
            404: view_spec.Responses.Error404,
        },
        parameters=[
            OpenApiParameter(
                name='id',
                type=str,
                location=OpenApiParameter.PATH,
                description='The source repo\'s id for this activity',
            ),
        ],
    )
    @action(detail=True, methods=['post'])
    def relations(self, request, *args, **kwargs):
        try:
            activity = Activity.objects.get(
                source_repo_entry_id=kwargs['pk'],
                source_repo_id=request.META.get('HTTP_X_API_CLIENT'),
            )
        except Activity.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        if (related_to := request.data.get('related_to')) is None:
            return Response(
                {'related_to': ['This field is required']},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if type(related_to) is not list:
            return Response(
                {'related_to': ['Has to be a list of repo entry ids']},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # check first if all items are strings before we change anything
        for related in related_to:
            if type(related) is not str:
                return Response(
                    {'related_to': 'Must only contain strings'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        # Now clear all existing relations and add the new ones
        activity.relations_to.clear()
        relations_added = []
        relations_not_added = []
        for related in related_to:
            if type(related) is not str:
                return Response(
                    {'related_to': 'Must only contain strings'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                related_activity = Activity.objects.get(
                    source_repo_entry_id=related,
                    source_repo_id=request.META.get('HTTP_X_API_CLIENT'),
                )
                relations_added.append(related)
                activity.relations_to.add(related_activity)
            except Activity.DoesNotExist:
                relations_not_added.append(related)

        ret = {
            'created': relations_added,
            'not_found': relations_not_added,
        }
        return Response(ret, status=status.HTTP_201_CREATED)


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
)
class AlbumViewSet(viewsets.ModelViewSet):
    queryset = Album.objects.all()
    serializer_class = AlbumSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(exclude=True)
    def list(self, request, *args, **kwargs):
        # Similar to list in EntitiyViewSet
        raise MethodNotAllowed(method='GET')


class MediaViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Media.objects.all()
    serializer_class = MediaSerializer
    permission_classes = [ActivityPermission]

    @extend_schema(
        tags=['repo'],
        # TODO: create own MediaCreateSerializer for the request body
        responses={
            201: MediaSerializer,  # TODO: create own MediaCreateResponse
            400: view_spec.Responses.Error400,
            403: view_spec.Responses.Error403,
            404: view_spec.Responses.Error404,
        },
    )
    def create(self, request, *args, **kwargs):
        # before we can provide the data to the serializer, we have to find
        # the activity that corresponds to the submitted source_repo_entry_id
        if not (source_repo_entry_id := request.data.get('source_repo_entry_id')):
            return Response(
                {'source_repo_entry_id': ['This field is required.']},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            activity = Activity.objects.get(source_repo_entry_id=source_repo_entry_id)
        except Activity.DoesNotExist:
            return Response(
                {
                    'source_repo_entry_id': [
                        'No activity with this source_repo_entry_id found.'
                    ]
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        request.data['activity'] = activity.id
        # now get the serializer and process the data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            instance = Media.objects.get(
                source_repo_media_id=serializer.validated_data['source_repo_media_id'],
                activity_id=activity.id,
            )
            serializer.instance = instance
        except Media.DoesNotExist:
            instance = False
        except Media.MultipleObjectsReturned:
            return Response(
                {
                    'detail': 'More than one medium with this id exists. '
                    + 'This should not happen. Contact the showroom admin.'
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
                    'id': serializer.validated_data['source_repo_media_id'],
                    'showroom_id': serializer.data['id'],
                }
            )
        else:
            response['created'].append(
                {
                    'id': serializer.validated_data['source_repo_media_id'],
                    'showroom_id': serializer.data['id'],
                }
            )

        return Response(response, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=['repo'],
        parameters=[
            OpenApiParameter(
                name='id',
                type=str,
                location=OpenApiParameter.PATH,
                description='The source repo\'s id for this activity',
            ),
        ],
        responses={
            204: None,
            400: view_spec.Responses.Error400,
            403: view_spec.Responses.Error403,
            404: view_spec.Responses.Error404,
        },
    )
    def destroy(self, request, *args, **kwargs):
        print(kwargs)
        try:
            instance = Media.objects.get(
                source_repo_media_id=kwargs['pk'],
                activity__source_repo=request.META.get('HTTP_X_API_CLIENT'),
            )
        except Media.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SearchViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Submit a search to Showroom."""

    serializer_class = view_spec.SearchSerializer

    @extend_schema(
        tags=['public'],
        responses={
            200: view_spec.Responses.SearchCollection,
            400: view_spec.Responses.Error400,
        },
    )
    def create(self, request, *args, **kwargs):
        s = view_spec.SearchSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        limit = s.data.get('limit')
        offset = s.data.get('offset')
        lang = request.LANGUAGE_CODE
        queryset = Activity.objects.all()
        if limit is not None or offset is not None:
            if offset is None:
                offset = 0
            elif offset >= len(queryset):
                return Response({'detail': 'offset too high'}, status=400)
            elif offset < 0:
                return Response({'detail': 'negative offset not allowed'}, status=400)
            if limit is None:
                end = len(queryset)
            elif limit < 1:
                return Response(
                    {'detail': 'negative or zero limit not allowed'}, status=400
                )
            elif offset + limit < len(queryset):
                end = offset + limit
            else:
                end = len(queryset)
            queryset = queryset[offset:end]
        response = {
            'label': 'All Showroom Activities',
            'total': len(queryset),
            'data': [],
        }
        for activity in queryset:
            activity_type = '' if not activity.type else activity.type['label'][lang]
            item = {
                'id': activity.id,
                'type': 'activity',
                'date_created': activity.date_created,
                'title': activity.title,
                'description': activity_type,
                'imageUrl': '',
                'href': '',
                'previews': [],
            }
            response['data'].append(item)
        return Response(response, status=200)


class FilterViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Get all the available filters that can be used in search and
    autocomplete."""

    @extend_schema(
        tags=['public'],
        responses={
            200: view_spec.Responses.Filters,
        },
    )
    def list(self, request, *args, **kwargs):
        return Response({'detail': 'Not yet implemented'}, status=400)


class AutocompleteViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Retrieves available autocomplete results for a specific string and
    filter."""

    @extend_schema(
        tags=['public'],
        responses={
            200: view_spec.Responses.AutoComplete,
        },
    )
    def create(self, request, *args, **kwargs):
        return Response({'detail': 'Not yet implemented'}, status=400)
