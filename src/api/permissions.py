from rest_framework import permissions

from core.models import SourceRepository


class ActivityPermission(permissions.BasePermission):
    """Checks that only source repos may POST and DELETE activities."""

    def has_permission(self, request, view):
        if request.method in ('POST', 'DELETE'):
            if (
                'X-Api-Client' not in request.headers
                or 'X-Api-Key' not in request.headers
            ):
                return False
            try:
                repo = SourceRepository.objects.get(pk=request.headers['X-Api-Client'])
            except SourceRepository.DoesNotExist:
                return False
            if request.headers['X-Api-Key'] != repo.api_key:
                return False
        return True
