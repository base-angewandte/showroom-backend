from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from api.serializers.album import AlbumSerializer
from api.serializers.generic import Responses
from core.models import ShowroomObject


class AlbumViewSet(viewsets.GenericViewSet):
    queryset = ShowroomObject.active_objects.filter(type=ShowroomObject.ALBUM)
    serializer_class = AlbumSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(exclude=True)
    def list(self, request, *args, **kwargs):
        # Similar to list in EntityViewSet
        raise MethodNotAllowed(method='GET')

    @extend_schema(
        tags=['public'],
        responses={
            200: AlbumSerializer,
            404: Responses.Error404,
        },
    )
    def retrieve(self, request, *args, **kwargs):
        return Response({'detail': 'not yet implemented'})

    @extend_schema(
        tags=['auth'],
        responses={
            201: AlbumSerializer,
            400: Responses.Error400,
            403: Responses.Error403,
        },
    )
    def create(self, request, *args, **kwargs):
        return Response({'detail': 'not yet implemented'})

    @extend_schema(
        tags=['auth'],
        responses={
            204: None,
            400: Responses.Error400,
            403: Responses.Error403,
            404: Responses.Error404,
        },
    )
    def destroy(self, request, *args, **kwargs):
        return Response({'detail': 'not yet implemented'})

    @extend_schema(
        tags=['auth'],
        responses={
            200: AlbumSerializer,
            400: Responses.Error400,
            403: Responses.Error403,
            404: Responses.Error404,
        },
    )
    def partial_update(self, request, *args, **kwargs):
        return Response({'detail': 'not yet implemented'})
