from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from api.permissions import HasPluginAPIKey
from api.repositories.portfolio.utils import get_usernames_from_roles
from api.serializers.media import MediaSerializer
from core.models import ShowroomObject


class RepoSourceSerializer(serializers.Serializer):
    title = serializers.CharField()
    subtitle = serializers.CharField(required=False)
    type = serializers.JSONField(required=False)
    keywords = serializers.JSONField(required=False)
    texts = serializers.JSONField(required=False)
    data = serializers.JSONField(required=False)
    _showroom_id = serializers.CharField()
    _publishing_info = serializers.JSONField()
    _media = serializers.JSONField()
    _relations = serializers.JSONField()
    _entity_mapping = serializers.JSONField()


@extend_schema(
    tags=['api_plugin'],
    parameters=[
        OpenApiParameter(
            'id',
            OpenApiTypes.STR,
            OpenApiParameter.PATH,
            description='A unique value identifying this showroom object.',
        )
    ],
)
class RepoSourceView(APIView):
    permission_classes = [HasPluginAPIKey]
    serializer_class = RepoSourceSerializer

    def get(self, request, *args, **kwargs):
        """Retrieve activity in the schema originally provided by the
        repository.

        Properties additionally added by Showroom are preceded with `_`,
        e.g. the `_showroom_id` or the `_publishing_info`. This endpoint
        is only available for clients authenticated with an API key
        configured for the repo_source API plugin.
        """
        self.check_object_permissions(request, 'repo_source')

        try:
            activity = ShowroomObject.active_objects.get(
                type=ShowroomObject.ACTIVITY,
                pk=kwargs['pk'],
            )
        except ShowroomObject.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)

        ret = activity.source_repo_data
        ret['_showroom_id'] = activity.showroom_id
        ret['_publishing_info'] = {
            'publisher': {
                'repo_source_id': activity.source_repo_owner_id,
            },
            'date_published': activity.date_created,
            'date_updated': activity.date_synced,
        }
        if activity.belongs_to:
            ret['_publishing_info']['publisher'][
                'showroom_id'
            ] = activity.belongs_to.showroom_id
            ret['_publishing_info']['publisher']['name'] = activity.belongs_to.title

        media = activity.media_set.all()
        media_entries = []
        if media:
            context = {
                'repo_base': activity.source_repo.url_repository,
                'request': request,
            }
            media_entries = MediaSerializer(media, many=True, context=context).data
        ret['_media'] = media_entries

        ret['_relations'] = {'to': [], 'from': []}
        for relation in activity.relations_to.filter(type=ShowroomObject.ACTIVITY):
            ret['_relations']['to'].append(relation.showroom_id)
        for relation in activity.relations_from.filter(type=ShowroomObject.ACTIVITY):
            ret['_relations']['from'].append(relation.showroom_id)

        ret['_entity_mapping'] = {}
        for username in get_usernames_from_roles(activity):
            try:
                entity = ShowroomObject.objects.get(source_repo_object_id=username)
                ret['_entity_mapping'][username] = entity.showroom_id
            except ShowroomObject.DoesNotExist:
                pass

        return Response(ret, status=200)
