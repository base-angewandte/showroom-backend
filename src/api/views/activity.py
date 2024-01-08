import logging
from datetime import datetime, timedelta

from django_rq import get_queue
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.response import Response
from rq.exceptions import NoSuchJobError
from rq.registry import ScheduledJobRegistry

from django.conf import settings
from django.db.utils import IntegrityError
from django.utils import timezone

from api.permissions import ApiKeyPermission
from api.repositories.portfolio.search_indexer import index_activity
from api.repositories.portfolio.utils import get_usernames_from_roles
from api.repositories.user_preferences.sync import pull_user_data
from api.serializers.activity import ActivityRelationSerializer, ActivitySerializer
from api.serializers.generic import Responses
from core.models import ContributorActivityRelations, ShowroomObject

publishing_log = logging.getLogger('publishing_log')
logger = logging.getLogger(__name__)


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
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = ShowroomObject.active_objects.filter(type=ShowroomObject.ACTIVITY)
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
        already_published = False
        try:
            instance, created = ShowroomObject.objects.get_or_create(
                source_repo_object_id=serializer.validated_data[
                    'source_repo_object_id'
                ],
                source_repo=serializer.validated_data['source_repo'],
                defaults={'type': ShowroomObject.ACTIVITY},
            )
            serializer.instance = instance
            if not created and instance.active:
                already_published = True
        except ShowroomObject.MultipleObjectsReturned:
            return Response(
                {
                    'detail': 'More than one activity with this id exists. '
                    + 'This should not happen. Contact the showroom admin.'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        serializer.save(date_synced=timezone.now(), active=True)

        # log the publication activity in our separate publishing.log
        pub_user = serializer.validated_data.get('source_repo_owner_id')
        if not already_published:
            publishing_log.info(f'{serializer.instance.id} published by {pub_user}')
        else:
            publishing_log.info(f'{serializer.instance.id} updated by {pub_user}')

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

        # (re)generate the contributor relations to this activity
        contributor_names = get_usernames_from_roles(serializer.instance)
        # TODO: check if we want to improve speed here by implementing a bulk delete
        ContributorActivityRelations.objects.filter(
            activity=serializer.instance
        ).exclude(contributor_source_id__in=contributor_names).delete()
        relations = [
            ContributorActivityRelations(
                contributor_source_id=contributor,
                activity_id=serializer.instance.id,
            )
            for contributor in contributor_names
        ]
        ContributorActivityRelations.objects.bulk_create(
            relations, ignore_conflicts=True
        )

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
                    try:
                        registry.remove(job_id, delete_job=True)
                    except NoSuchJobError:
                        pass
                queue.enqueue_in(
                    timedelta(seconds=settings.WORKER_DELAY_ENTITY),
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
        if not created and already_published:
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
        if not activity.active:
            return Response(
                {'detail': 'Activity already deactivated.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        entity = activity.belongs_to
        activity.deactivate()
        if entity and entity.active:
            entity.entitydetail.enqueue_list_render_job()

        publishing_log.info(f'{activity.id} unpublished')
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
            activity = ShowroomObject.active_objects.get(
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
        relations_error = []
        for related in related_to:
            if type(related) is not str:
                return Response(
                    {'related_to': 'Must only contain strings'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                related_activity = ShowroomObject.active_objects.get(
                    source_repo_object_id=related,
                    source_repo_id=request.META.get('HTTP_X_API_CLIENT'),
                )
                activity.relations_to.add(related_activity)
                relations_added.append(related)
            except ShowroomObject.DoesNotExist:
                relations_not_added.append(related)
            except IntegrityError as err:
                # TODO: this case should not happen, as the RelatedManager should handle this
                #   gracefully. But we ran into some rare edge cases where this did occur (maybe a
                #   postgres issue?)
                #   added this exception on 2024-01-08
                #   check the logs for these errors in the next year and discuss how to proceed
                relations_error.append(related)
                errinfo = f'Current relations of activity {activity} are: {activity.relations_to.all()}'
                logger.error(
                    f'Could not add relation due to IntegrityError: {err} Additional info: {errinfo}'
                )

        ret = {
            'created': relations_added,
            'not_found': relations_not_added,
            'error': relations_error,
        }
        return Response(ret, status=status.HTTP_201_CREATED)
