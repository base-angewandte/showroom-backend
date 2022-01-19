from rest_framework import permissions

from django.conf import settings

from core.models import Entity, SourceRepository


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


class EntityEditPermission(permissions.BasePermission):
    """Checks that a logged in user is only allowed to edit their own
    entities."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        pk = view.kwargs['pk'].split('-')[-1]
        # TODO: discuss: theoretically there could be more than one entity
        #       associated to one user. also there could be users with the same
        #       ID from different repositories. how do we want to handle that?
        entities = Entity.objects.filter(source_repo_entry_id=request.user.username)
        if not entities:
            return False
        allowed = [entity.id for entity in entities]
        if request.user.username in settings.SHOWCASE_DEMO_USERS:
            allowed.extend(settings.SHOWCASE_DEMO_ENTITY_EDITING)
        if pk in allowed:
            return True
        return False
