from rest_framework import permissions

from django.conf import settings

from core.models import ShowroomObject, SourceRepository


class ApiKeyPermission(permissions.BasePermission):
    """Checks that only source repos may create and modify showroom objects."""

    def has_permission(self, request, view):
        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            if not request.headers.get('X-Api-Key'):
                return False

            if not SourceRepository.objects.filter(
                api_key=request.headers['X-Api-Key']
            ).exists():
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
        entities = ShowroomObject.active_objects.filter(
            type=ShowroomObject.PERSON, source_repo_object_id=request.user.username
        )
        # if not entities:
        #     return False
        allowed = [entity.id for entity in entities]
        if request.user.username in settings.SHOWCASE_DEMO_USERS:
            allowed.extend(settings.SHOWCASE_DEMO_ENTITY_EDITING)
        if pk in allowed:
            return True
        return False
