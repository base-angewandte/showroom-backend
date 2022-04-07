from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.response import Response

from api.permissions import ActivityPermission
from api.serializers.generic import Responses
from api.serializers.media import MediaSerializer
from core.models import Media, ShowroomObject


class MediaViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Media.objects.all()
    serializer_class = MediaSerializer
    permission_classes = [ActivityPermission]

    @extend_schema(
        tags=['repo'],
        # TODO: create own MediaCreateSerializer for the request body
        responses={
            201: MediaSerializer,  # TODO: create own MediaCreateResponse
            400: Responses.Error400,
            403: Responses.Error403,
            404: Responses.Error404,
        },
    )
    def create(self, request, *args, **kwargs):
        # before we can provide the data to the serializer, we have to find
        # the activity that corresponds to the submitted source_repo_entry_id
        if not (source_repo_entry_id := request.data.get('source_repo_entry_id')):
            return Response(
                {'source_repo_entry_id': ['This field is required.']},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            activity = ShowroomObject.objects.get(
                source_repo_object_id=source_repo_entry_id
            )
        except ShowroomObject.DoesNotExist:
            return Response(
                {
                    'source_repo_entry_id': [
                        'No activity with this source_repo_entry_id found.'
                    ]
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        request.data['showroom_object'] = activity.id
        # now get the serializer and process the data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            instance = Media.objects.get(
                source_repo_media_id=serializer.validated_data['source_repo_media_id'],
                showroom_object=activity,
            )
            serializer.instance = instance
        except Media.DoesNotExist:
            instance = False
        except Media.MultipleObjectsReturned:
            return Response(
                {
                    'detail': 'More than one medium with this id exists. '
                    + 'This should not happen. Contact the showroom admin.'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        serializer.save()

        # in case featured was set, we have to clear it in any other media of the same
        # showroom_object
        if request.data.get('featured'):
            Media.objects.filter(showroom_object=activity).exclude(
                source_repo_media_id=serializer.validated_data['source_repo_media_id']
            ).update(featured=False)

        response = {
            'created': [],
            'updated': [],
            'errors': [],
        }
        if instance:
            response['updated'].append(
                {
                    'id': serializer.validated_data['source_repo_media_id'],
                    'showroom_id': serializer.data['id'],
                }
            )
        else:
            response['created'].append(
                {
                    'id': serializer.validated_data['source_repo_media_id'],
                    'showroom_id': serializer.data['id'],
                }
            )

        return Response(response, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=['repo'],
        parameters=[
            OpenApiParameter(
                name='id',
                type=str,
                location=OpenApiParameter.PATH,
                description='The source repo\'s id for this activity',
            ),
        ],
        responses={
            204: None,
            400: Responses.Error400,
            403: Responses.Error403,
            404: Responses.Error404,
        },
    )
    def destroy(self, request, *args, **kwargs):
        try:
            instance = Media.objects.get(
                source_repo_media_id=kwargs['pk'],
                showroom_object__source_repo=request.META.get('HTTP_X_API_CLIENT'),
            )
        except Media.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
