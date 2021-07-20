from drf_spectacular.utils import extend_schema
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import Entity


class UserViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Return a logged in user's metadata."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['auth'],
    )
    def list(self, request, *args, **kwargs):
        attributes = request.session.get('attributes')
        try:
            entity = Entity.objects.get(source_repo_entry_id=request.user.username)
            entity_id = entity.id
        except Entity.DoesNotExist:
            entity_id = None
        ret = {
            'id': request.user.username,
            'name': attributes.get('display_name'),
            'email': attributes.get('email'),
            'entity_id': entity_id,
        }
        return Response(ret, status=200)
