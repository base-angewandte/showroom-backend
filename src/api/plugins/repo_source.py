from rest_framework.response import Response
from rest_framework.views import APIView

from api.permissions import HasPluginAPIKey


class RepoSourceView(APIView):
    permission_classes = [HasPluginAPIKey]

    def get(self, request, *args, **kwargs):
        self.check_object_permissions(request, 'repo_source')
        return Response({'detail': 'not yet implemented'}, status=200)
