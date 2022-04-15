from datetime import datetime, timedelta

from django_rq import get_queue
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.response import Response
from rq.registry import ScheduledJobRegistry

from django.conf import settings

from api.permissions import ApiKeyPermission
from api.repositories.portfolio.search_indexer import index_activity
from api.repositories.user_preferences.sync import pull_user_data
from api.serializers.activity import ActivityRelationSerializer, ActivitySerializer
from api.serializers.generic import Responses
from core.models import ShowroomObject


@extend_schema_view(
    retrieve=extend_schema(
        tags=['public'],
        responses={
            200: ActivitySerializer,
            404: Responses.Error404,
        },
    ),
)
class ActivityViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = ShowroomObject.objects.filter(type=ShowroomObject.ACTIVITY)
    serializer_class = ActivitySerializer
    permission_classes = [ApiKeyPermission]

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
            instance = ShowroomObject.objects.get(
                source_repo_object_id=serializer.validated_data[
                    'source_repo_object_id'
                ],
                source_repo=serializer.validated_data['source_repo'],
            )
            serializer.instance = instance
        except ShowroomObject.DoesNotExist:
            instance = False
        except ShowroomObject.MultipleObjectsReturned:
            return Response(
                {
                    'detail': 'More than one activity with this id exists. '
                    + 'This should not happen. Contact the showroom admin.'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        serializer.save()

        # now fill the ActivityDetail belonging to this ShowroomObject
        repo_data = serializer.instance.source_repo_data
        serializer.instance.activitydetail.activity_type = repo_data.get('type')
        serializer.instance.activitydetail.keywords = (
            {
                kw['label'][settings.LANGUAGE_CODE]: True
                for kw in repo_data.get('keywords')
            }
            if repo_data.get('keywords')
            else {}
        )
        serializer.instance.activitydetail.save()

        # as soon as the serializer is saved we want the full text search index to be
        # built. TODO: refactor this to an async worker
        index_activity(serializer.instance)

        if not settings.DISABLE_USER_REPO:
            if serializer.instance.belongs_to:
                # in case the entity is already in the system, we'll sync it from UP
                # if the current version is older than the configured sync time
                serializer.instance.belongs_to.entitydetail.enqueue_list_render_job()
                t_synced = serializer.instance.belongs_to.date_synced
                t_cache = datetime.today() - timedelta(
                    minutes=settings.USER_REPO_CACHE_TIME
                )
                if t_synced is None or t_synced.timestamp() < t_cache.timestamp():
                    queue = get_queue('default')
                    queue.enqueue(
                        pull_user_data,
                        username=serializer.instance.source_repo_owner_id,
                    )

            else:
                # in case the entity is not in the system yet, we fetch it from UP,
                # but with a small delay, so in case many activities are pushed at
                # once, the sync job for the entity is only executed after the last
                # activity was pushed
                job_id = f'entity_sync_{serializer.instance.source_repo_owner_id}'
                queue = get_queue('default')
                registry = ScheduledJobRegistry(queue=queue)
                if job_id in registry:
                    registry.remove(job_id)
                queue.enqueue_in(
                    timedelta(seconds=settings.WORKER_DELAY_ENTITY_LIST),
                    pull_user_data,
                    username=serializer.instance.source_repo_owner_id,
                    job_id=job_id,
                )
        # in case the user repo is turned off, we nevertheless want to check, if there
        # is already an entity in the system, for which we can generate a new list
        else:
            if serializer.instance.belongs_to:
                serializer.instance.belongs_to.entitydetail.enqueue_list_render_job()

        response = {
            'created': [],
            'updated': [],
            'errors': [],
        }
        if instance:
            response['updated'].append(
                {
                    'id': serializer.validated_data['source_repo_object_id'],
                    'showroom_id': serializer.data['id'],
                }
            )
        else:
            response['created'].append(
                {
                    'id': serializer.validated_data['source_repo_object_id'],
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
            activity = ShowroomObject.objects.get(
                source_repo_object_id=kwargs['pk'],
                source_repo_id=request.META.get('HTTP_X_API_CLIENT'),
            )
        except ShowroomObject.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        rerender_list = True if activity.belongs_to else False
        self.perform_destroy(activity)
        if rerender_list:
            activity.belongs_to.enqueue_list_render_job()
        return Response(status=status.HTTP_204_NO_CONTENT)

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
            activity = ShowroomObject.objects.get(
                source_repo_object_id=kwargs['pk'],
                source_repo_id=request.META.get('HTTP_X_API_CLIENT'),
            )
        except ShowroomObject.DoesNotExist:
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
                related_activity = ShowroomObject.objects.get(
                    source_repo_object_id=related,
                    source_repo_id=request.META.get('HTTP_X_API_CLIENT'),
                )
                relations_added.append(related)
                activity.relations_to.add(related_activity)
            except ShowroomObject.DoesNotExist:
                relations_not_added.append(related)

        ret = {
            'created': relations_added,
            'not_found': relations_not_added,
        }
        return Response(ret, status=status.HTTP_201_CREATED)
