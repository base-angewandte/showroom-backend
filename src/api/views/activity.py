from datetime import datetime, timedelta

from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.response import Response

from api.permissions import ActivityPermission
from api.repositories.portfolio.search_indexer import index_activity
from api.repositories.user_preferences.sync import pull_user_data
from api.serializers.activity import ActivityRelationSerializer, ActivitySerializer
from api.serializers.generic import Responses
from api.serializers.media import MediaSerializer
from core.models import Activity


@extend_schema_view(
    retrieve=extend_schema(
        tags=['public'],
        responses={
            200: ActivitySerializer,
            404: Responses.Error404,
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
        # Similar to list in EntityViewSet
        raise MethodNotAllowed(method='GET')

    @extend_schema(
        tags=['repo'],
        responses={
            201: ActivitySerializer,
            400: Responses.Error400,
            403: Responses.Error403,
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
        # as soon as the serializer is saved we want the full text search index to be
        # built. TODO: refactor this to an async worker
        index_activity(serializer.instance)

        if serializer.instance.belongs_to:
            serializer.instance.belongs_to.enqueue_list_render_job()
            # TODO: make the caching time configurable
            date_mark = datetime.today() + timedelta(minutes=15)
            if (
                serializer.instance.belongs_to.date_changed.timestamp()
                < date_mark.timestamp()
            ):
                # TODO: convert to job
                pull_user_data(serializer.instance.source_repo_owner_id)
        else:
            # TODO: convert to job
            pull_user_data(serializer.instance.source_repo_owner_id)

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
            400: Responses.Error400,
            403: Responses.Error403,
            404: Responses.Error404,
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
        rerender_list = True if activity.belongs_to else False
        self.perform_destroy(activity)
        if rerender_list:
            activity.belongs_to.enqueue_list_render_job()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        tags=['public'],
        responses={
            200: MediaSerializer(many=True),
            404: Responses.Error404,
        },
    )
    @action(detail=True, methods=['get'])
    def media(self, request, *args, **kwargs):
        return Response({'detail': 'Not yet implemented'}, status=400)

    @extend_schema(
        tags=['repo'],
        request=ActivityRelationSerializer,
        responses={
            201: Responses.RelationAdded,
            400: Responses.Error400,
            404: Responses.Error404,
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
