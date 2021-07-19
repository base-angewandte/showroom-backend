from drf_spectacular.utils import extend_schema
from rest_framework import mixins, viewsets
from rest_framework.response import Response

from api import view_spec
from core.models import Activity


class SearchViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Submit a search to Showroom."""

    serializer_class = view_spec.SearchSerializer

    @extend_schema(
        tags=['public'],
        responses={
            200: view_spec.Responses.SearchCollection,
            400: view_spec.Responses.Error400,
        },
    )
    def create(self, request, *args, **kwargs):
        s = view_spec.SearchSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        limit = s.data.get('limit')
        offset = s.data.get('offset')
        lang = request.LANGUAGE_CODE
        queryset = Activity.objects.all()
        if limit is not None or offset is not None:
            if offset is None:
                offset = 0
            elif offset >= len(queryset):
                return Response({'detail': 'offset too high'}, status=400)
            elif offset < 0:
                return Response({'detail': 'negative offset not allowed'}, status=400)
            if limit is None:
                end = len(queryset)
            elif limit < 1:
                return Response(
                    {'detail': 'negative or zero limit not allowed'}, status=400
                )
            elif offset + limit < len(queryset):
                end = offset + limit
            else:
                end = len(queryset)
            queryset = queryset[offset:end]
        response = {
            'label': 'All Showroom Activities',
            'total': len(queryset),
            'data': [],
        }
        for activity in queryset:
            activity_type = '' if not activity.type else activity.type['label'][lang]
            item = {
                'id': activity.id,
                'type': 'activity',
                'date_created': activity.date_created,
                'title': activity.title,
                'description': activity_type,
                'imageUrl': '',
                'href': '',
                'previews': [],
            }
            response['data'].append(item)
        return Response(response, status=200)
