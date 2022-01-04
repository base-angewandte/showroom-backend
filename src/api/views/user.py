from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.serializers.generic import Responses
from api.serializers.user import UserDataSerializer
from core.models import Entity


@extend_schema(
    tags=['auth'],
    responses={
        200: UserDataSerializer,
        403: Responses.Error403,
    },
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_data(request, *args, **kwargs):
    attributes = request.session.get('attributes')
    if not attributes:
        return Response(
            {'detail': 'Authentication credentials were not provided.'}, status=403
        )

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
