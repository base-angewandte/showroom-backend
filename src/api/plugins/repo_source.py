from rest_framework.response import Response
from rest_framework.views import APIView

from api.permissions import HasPluginAPIKey
from core.models import ShowroomObject
from general.datetime.utils import format_datetime


class RepoSourceView(APIView):
    permission_classes = [HasPluginAPIKey]

    def get(self, request, *args, **kwargs):
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
            'publisher': activity.source_repo_owner_id,
            'date_published': format_datetime(activity.date_created),
            'date_updated': format_datetime(activity.date_synced),
        }

        return Response(ret, status=200)
