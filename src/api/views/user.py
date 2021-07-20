from drf_spectacular.utils import OpenApiExample, extend_schema, inline_serializer
from rest_framework import mixins, serializers, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api import view_spec
from core.models import Entity


class UserViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Return a logged in user's metadata."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['auth'],
        responses={
            200: inline_serializer(
                name='User',
                fields={
                    'id': serializers.CharField(),
                    'name': serializers.CharField(),
                    'email': serializers.CharField(),
                    'entry_id': serializers.CharField(),
                    'groups': serializers.ListSerializer(child=serializers.CharField()),
                    'permissions': serializers.ListSerializer(
                        child=serializers.CharField()
                    ),
                },
            ),
            403: view_spec.Responses.Error403,
        },
        examples=[
            OpenApiExample(
                name='User',
                value={
                    'id': 'source_repo_uuid',
                    'name': 'Firstname Lastname',
                    'email': 'addy@example.org',
                    'entry_id': 'showroom_entry_shortuuid_or_null',
                    'groups': ['foo_users', 'bar_members'],
                    'permissions': ['view_foo', 'view_bar', 'edit_bar'],
                },
                status_codes=['200'],
                response_only=True,
            ),
        ],
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
            'groups': attributes.get('groups'),
            'permissions': attributes.get('permissions'),
        }
        return Response(ret, status=200)
