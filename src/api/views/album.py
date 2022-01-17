from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from api.serializers.album import AlbumSerializer
from api.serializers.generic import Responses
from core.models import Album


@extend_schema_view(
    create=extend_schema(
        tags=['auth'],
        responses={
            201: AlbumSerializer,
            400: Responses.Error400,
            403: Responses.Error403,
        },
    ),
    partial_update=extend_schema(
        tags=['auth'],
        responses={
            200: AlbumSerializer,
            400: Responses.Error400,
            403: Responses.Error403,
            404: Responses.Error404,
        },
    ),
    destroy=extend_schema(
        tags=['auth'],
        responses={
            204: None,
            400: Responses.Error400,
            403: Responses.Error403,
            404: Responses.Error404,
        },
    ),
    retrieve=extend_schema(
        tags=['public'],
        responses={
            200: AlbumSerializer,
            404: Responses.Error404,
        },
    ),
    update=extend_schema(exclude=True),
)
class AlbumViewSet(viewsets.ModelViewSet):
    queryset = Album.objects.all()
    serializer_class = AlbumSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(exclude=True)
    def list(self, request, *args, **kwargs):
        # Similar to list in EntitiyViewSet
        raise MethodNotAllowed(method='GET')
