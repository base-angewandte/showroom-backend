from rest_framework import permissions

from core.models import SourceRepository


class ActivityPermission(permissions.BasePermission):
    """Checks that only source repos may create and modify activities."""

    def has_permission(self, request, view):
        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            if (
                'X-Api-Client' not in request.headers
                or 'X-Api-Key' not in request.headers
            ):
                return False
            if (
                request.headers['X-Api-Client'] == ''
                or request.headers['X-Api-Key'] == ''
            ):
                return False

            try:
                repo = SourceRepository.objects.get(pk=request.headers['X-Api-Client'])
            except SourceRepository.DoesNotExist:
                return False
            if request.headers['X-Api-Key'] != repo.api_key:
                return False

            # check whether the data contains a `source_repo` key and only
            # allow the operation if its value is the same
            if source_repo := request.data.get('source_repo'):
                if source_repo != repo.id:
                    return False
        return True
