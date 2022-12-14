from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.conf import settings

from api.serializers.generic import Responses
from api.serializers.user import UserDataSerializer
from core.models import ShowroomObject


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
        entity = ShowroomObject.objects.get(
            type=ShowroomObject.PERSON, source_repo_object_id=request.user.username
        )
        entity_id = entity.id
        showroom_id = entity.showroom_id if entity.active else None
    except ShowroomObject.DoesNotExist:
        entity_id = None
        showroom_id = None
    except ShowroomObject.MultipleObjectsReturned:
        # TODO: discuss: how do we want to handle multiple Entities with the same
        #       user set as source_repo_entry_id. See also the similar comment in the
        #       api.permissions.EntityEditPermission class
        #       For simplicity we'll currently just take the first found entity
        entities = ShowroomObject.objects.filter(
            type=ShowroomObject.PERSON, source_repo_object_id=request.user.username
        )
        entity_id = entities[0].id
        showroom_id = entities[0].showroom_id if entities[0].active else None
    ret = {
        'id': request.user.username,
        'name': attributes.get('display_name'),
        'email': attributes.get('email'),
        'entity_id': entity_id,
        'showroom_id': showroom_id,
        'entity_editing': [showroom_id] if showroom_id else [],
        'groups': attributes.get('groups'),
        'permissions': attributes.get('permissions'),
    }
    if request.user.username in settings.SHOWCASE_DEMO_USERS:
        ret['entity_editing'].extend(settings.SHOWCASE_DEMO_ENTITY_EDITING)
    return Response(ret, status=200)
