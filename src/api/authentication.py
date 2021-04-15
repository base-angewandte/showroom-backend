from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from core.models import SourceRepository

# TODO: decide if we should keep this and modify the ActivityViewSet
# currently this is not used, as it is quite redundant to what the ActivityPermission already does


class SourceRepoAuthentication(BaseAuthentication):
    def authenticate(self, request):

        # Get the username and password
        api_user = request.META.get('X-Api-User', None)
        api_key = request.META.get('X-Api-Key', None)

        if not api_user or not api_key:
            return None

        if not api_user:
            raise AuthenticationFailed('X-Api-User header is missing')
        if not api_key:
            raise AuthenticationFailed('X-Api-Key header is missing')

        try:
            repo = SourceRepository.objects.get(pk=api_user)
        except SourceRepository.DoesNotExist:
            raise AuthenticationFailed('API credentials are not valid')

        if api_key != repo.api_key:
            raise AuthenticationFailed('API credentials are not valid')

        return None
