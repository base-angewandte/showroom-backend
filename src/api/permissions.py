from rest_framework import permissions
from rest_framework_api_key.permissions import BaseHasAPIKey

from django.conf import settings

from api.models import PluginAPIKey
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
        pk = view.kwargs['pk']
        # TODO: discuss: theoretically there could be more than one entity
        #       associated to one user. also there could be users with the same
        #       ID from different repositories. how do we want to handle that?
        entities = ShowroomObject.active_objects.filter(
            type=ShowroomObject.PERSON, source_repo_object_id=request.user.username
        )
        # if not entities:
        #     return False
        allowed = [entity.showroom_id for entity in entities]
        if request.user.username in settings.SHOWCASE_DEMO_USERS:
            allowed.extend(settings.SHOWCASE_DEMO_ENTITY_EDITING)
        if pk in allowed:
            return True
        return False


class HasPluginAPIKey(BaseHasAPIKey):
    model = PluginAPIKey

    def has_object_permission(self, request, view, plugin) -> bool:
        key = self.get_key(request)
        api_key = self.model.objects.get_from_key(key)

        # check whether the api key is currently active
        if not api_key.active:
            return False

        # check whether the api key is allowed to use the specific plugin
        if plugin not in api_key.plugins:
            return False

        # check whether the client IP is allowed to use this api key
        if '*' not in api_key.allowed_ips:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
            if ip not in api_key.allowed_ips:
                return False

        return True
