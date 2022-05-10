import logging

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed, NotFound, ParseError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from django.conf import settings
from django.core.exceptions import ValidationError

from api.permissions import ApiKeyPermission, EntityEditPermission
from api.repositories.portfolio import activity_lists
from api.serializers.autocomplete import (
    AutocompleteRequestSerializer,
    AutocompleteSerializer,
)
from api.serializers.entity import (
    EntityEditSerializer,
    EntityListEditSerializer,
    EntitySerializer,
)
from api.serializers.filter import FilterSerializer
from api.serializers.generic import CommonListEditSerializer, Responses
from api.serializers.search import SearchRequestSerializer, SearchResultSerializer
from api.serializers.showcase import ShowcaseSerializer
from api.views.autocomplete import AutocompleteViewSet
from api.views.filter import get_dynamic_entity_filters, static_entity_filters
from api.views.search import CsrfExemptSessionAuthentication, get_search_results
from core.models import ShowroomObject, SourceRepository
from core.validators import validate_showcase
from general.utils import slugify

logger = logging.getLogger(__name__)


class EntityViewSet(viewsets.GenericViewSet):
    queryset = ShowroomObject.active_objects.filter(
        type__in=[
            ShowroomObject.PERSON,
            ShowroomObject.DEPARTMENT,
            ShowroomObject.INSTITUTION,
        ]
    )
    serializer_class = EntitySerializer
    # Entities should be only manipulated by repositories, similar to Activities, so
    # we'll reuse ActivityPermission and use other permissions explicitly on all custom
    # actions, when needed
    permission_classes = [ApiKeyPermission]
    # we only want partial updates enabled, therefore removing put
    # from the allowed methods
    http_method_names = ['get', 'head', 'options', 'patch', 'post', 'put']

    @extend_schema(exclude=True)
    def list(self, request, *args, **kwargs):
        # If we do not include the ListModelMixin and define this here, Django would
        # provide a standard 404 HTML page. So to be consistent with the APIs error
        # scheme we raise a rest_framework 405, and exclude the list method in the
        # schema (through the list parameter in the extend_schema_view decorator
        # above)
        raise MethodNotAllowed(method='GET')

    @extend_schema(
        tags=['public'],
        responses={
            200: EntitySerializer(),
            404: Responses.Error404,
        },
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object_or_404(pk=kwargs['pk'])
        # if not settings.DISABLE_USER_REPO and instance.type == ShowroomObject.PERSON:
        #     try:
        #         sync.pull_user_data(instance.source_repo_object_id)
        #     except sync.UserPrefError:
        #         # TODO: discuss what to do if the sync fails but we already have some data
        #         pass
        #     # TODO: deactivated the code below for now, because we have to check user
        #     #       settings on every request, to see if their user page is activiated.
        #     #       this can be changed back, as soon as there is a push from UP to SR,
        #     #       whenever the setting changes
        #     # t_synced = instance.date_synced
        #     # t_cache = datetime.today() - timedelta(
        #     #     minutes=settings.USER_REPO_CACHE_TIME
        #     # )
        #     # if t_synced is None or t_synced.timestamp() < t_cache.timestamp():
        #     #     # TODO: discuss whether this should be executed directly or relegated to an async
        #     #     #       job. in the latter case the current request would be served the cached data
        #     #     try:
        #     #         sync.pull_user_data(instance.source_repo_object_id)
        #     #     except sync.UserPrefError:
        #     #         # TODO: discuss what to do if the sync fails but we already have some data
        #     #         pass
        # instance.refresh_from_db()

        if not instance.active:
            return Response(
                {'detail': 'user has deactivated their profile page'}, status=404
            )

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @extend_schema(
        tags=['repo'],
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description='The source repo\'s id for this entity',
            ),
        ],
        request=OpenApiTypes.OBJECT,  # TODO: use PolymorphicProxySerializer to support different repositories
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.STR, description='Showroom id of this entity'
            ),
            201: OpenApiResponse(
                response=OpenApiTypes.STR, description='Showroom id of this entity'
            ),
            400: Responses.Error400,
            403: Responses.Error403,
        },
    )
    def update(self, request, pk, *args, **kwargs):
        try:
            source_repo = SourceRepository.objects.get(
                api_key=request.META.get('HTTP_X_API_KEY')
            )
        except SourceRepository.DoesNotExist:
            # this case should not be happening, as the key is already validated
            return Response(status=status.HTTP_403_FORBIDDEN)

        entity, created = ShowroomObject.objects.get_or_create(
            source_repo_object_id=pk,
            source_repo=source_repo,
            defaults={'type': ShowroomObject.PERSON},
        )
        entity.source_repo_data = request.data
        entity.save()
        entity.entitydetail.run_updates()

        return Response(entity.showroom_id, status=201 if created else 200)

    @extend_schema(
        methods=['GET'],
        # TODO: check why autogeneration is doing a list instead of retrieve here
        operation_id='api_v1_entities_list_retrieve',
    )
    @extend_schema(
        tags=['auth'],
        request=EntityListEditSerializer(many=True),
        responses={
            200: CommonListEditSerializer(many=True),
            403: Responses.Error403,
            404: Responses.Error404,
        },
    )
    @action(
        detail=True,
        methods=['get', 'patch'],
        url_path='list',
        permission_classes=[EntityEditPermission],
        authentication_classes=[CsrfExemptSessionAuthentication],
    )
    def activities_list(self, request, *args, **kwargs):
        instance = self.get_object_or_404(pk=kwargs['pk'])

        # GET /entities/{id}/list
        if request.method.lower() == 'get':
            return Response(
                instance.entitydetail.get_editing_list(lang=self.request.LANGUAGE_CODE),
                status=200,
            )

        # PATCH /entities/{id}/list
        else:
            # validate data
            serializer = EntityListEditSerializer(data=request.data, many=True)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data

            # now add all active schemas that are not explicitly set as hidden items
            schemas = [item.get('id') for item in data]
            for schema in activity_lists.list_collections:
                if schema not in schemas:
                    data.append({'id': schema, 'hidden': True})

            # update entity
            instance.entitydetail.list_ordering = data
            instance.entitydetail.save()
            instance.entitydetail.render_list()

            return Response(
                instance.entitydetail.get_editing_list(lang=self.request.LANGUAGE_CODE),
                status=200,
            )

    @extend_schema(
        methods=['GET'],
        parameters=[
            OpenApiParameter(
                name='secondary_details',
                type=bool,
                default=False,
                location=OpenApiParameter.QUERY,
                description='Whether to include secondary_details in the response',
            ),
            OpenApiParameter(
                name='showcase',
                type=bool,
                default=False,
                location=OpenApiParameter.QUERY,
                description='Whether to include showcase in the response',
            ),
            OpenApiParameter(
                name='showcase_details',
                type=bool,
                default=False,
                location=OpenApiParameter.QUERY,
                description='Whether to include the pre-rendered showcase item details',
            ),
        ],
    )
    @extend_schema(
        tags=['auth'],
        request=EntityEditSerializer,
        responses={
            200: EntityEditSerializer,
            403: Responses.Error403,
            404: Responses.Error404,
        },
    )
    @action(
        detail=True,
        methods=['get', 'patch'],
        url_path='edit',
        permission_classes=[EntityEditPermission],
        authentication_classes=[CsrfExemptSessionAuthentication],
    )
    def edit(self, request, *args, **kwargs):
        instance = self.get_object_or_404(pk=kwargs['pk'])
        # GET /entities/{id}/edit
        if request.method.lower() == 'get':
            # validate query parameters
            include_showcase = False
            include_showcase_details = False
            include_secondary_details = False
            if 'showcase' in request.query_params:
                include_showcase = parse_boolean_query_param(
                    'showcase', request.query_params['showcase']
                )
            if 'showcase_details' in request.query_params:
                include_showcase_details = parse_boolean_query_param(
                    'showcase_details', request.query_params['showcase_details']
                )
            if 'secondary_details' in request.query_params:
                include_secondary_details = parse_boolean_query_param(
                    'secondary_details', request.query_params['secondary_details']
                )
            # now assemble the return dict
            ret = {}
            if include_secondary_details:
                ret['secondary_details'] = instance.secondary_details
            if include_showcase:
                ret['showcase'] = get_rendered_edit_showcase(
                    instance.entitydetail.showcase,
                    include_details=include_showcase_details,
                )

        # PATCH /entities/{id}/edit
        else:
            # validate data
            serializer = EntityEditSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data

            # update entity
            if (showcase := data.get('showcase')) is not None:
                instance.entitydetail.showcase = []
                for sc_item in showcase:
                    if 'type' not in sc_item:
                        sc_item['type'] = 'activity'
                    instance.entitydetail.showcase.append(
                        [sc_item['id'], sc_item['type']]
                    )
                try:
                    validate_showcase(instance.entitydetail.showcase)
                except ValidationError as err:
                    raise serializers.ValidationError({'showcase': err}) from err
                instance.entitydetail.save()
            if (secondary_details := data.get('secondary_details')) is not None:
                instance.secondary_details = secondary_details
            instance.save()

            # assemble the updated data for return
            ret = {}
            if secondary_details is not None:
                if not instance.secondary_details:
                    ret['secondary_details'] = [
                        {lang: [] for lang, _label in settings.LANGUAGES}
                    ]
                else:
                    ret['secondary_details'] = instance.secondary_details

            if showcase is not None:
                ret['showcase'] = get_rendered_edit_showcase(
                    instance.entitydetail.showcase, include_details=True
                )

        return Response(ret, status=200)

    @extend_schema(
        tags=['public'],
        responses={
            200: OpenApiResponse(
                description='',
                response=serializers.ListSerializer(child=AutocompleteSerializer()),
                # TODO: add description and examples
            ),
        },
    )
    @action(
        detail=True,
        methods=['post'],
        permission_classes=[AllowAny],
        authentication_classes=[CsrfExemptSessionAuthentication],
        serializer_class=AutocompleteRequestSerializer,
    )
    def autocomplete(self, request, *args, **kwargs):
        s = self.get_serializer(data=request.data)
        s.is_valid(raise_exception=True)
        instance = self.get_object_or_404(pk=kwargs['pk'])
        q = s.data.get('q')
        filter_id = s.data.get('filter_id')
        limit = s.data.get('limit')
        lang = request.LANGUAGE_CODE

        allowed_filters = ['fulltext', 'activity', 'person']
        if filter_id not in allowed_filters:
            return Response(
                {
                    'detail': f'{filter_id} is not an allowed autocomplete filter. allowed: {allowed_filters}',
                },
                status=400,
            )

        return Response(
            AutocompleteViewSet.get_results(
                ShowroomObject.active_objects.filter(belongs_to=instance),
                q,
                filter_id,
                limit,
                lang,
            ),
            status=200,
        )

    @extend_schema(
        tags=['public'],
        parameters=[
            OpenApiParameter(
                name='Accept-Language',
                type=str,
                default=settings.LANGUAGE_CODE,
                location=OpenApiParameter.HEADER,
                description='The ISO 2 letter language code to use for localisation',
            ),
        ],
        responses={
            200: FilterSerializer,
        },
    )
    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def filters(self, request, *args, **kwargs):
        instance = self.get_object_or_404(pk=kwargs['pk'])

        lang = request.LANGUAGE_CODE
        if lang not in [ln[0] for ln in settings.LANGUAGES]:
            lang = settings.LANGUAGE_CODE

        filters = [
            {
                key: (value if key != 'label' else value[lang])
                for key, value in _filter.items()
            }
            for _filter in static_entity_filters
        ]
        filters.extend(get_dynamic_entity_filters(instance, lang=lang))
        return Response(filters, status=200)

    @extend_schema(
        tags=['public'],
        responses={
            200: SearchResultSerializer(many=True),
            404: Responses.Error404,
        },
        # TODO: change parameters
    )
    @action(
        detail=True,
        methods=['post'],
        permission_classes=[AllowAny],
        authentication_classes=[CsrfExemptSessionAuthentication],
    )
    def search(self, request, *args, **kwargs):
        s = SearchRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        instance = self.get_object_or_404(pk=kwargs['pk'])
        filters = s.data.get('filters')
        limit = s.data.get('limit')
        offset = s.data.get('offset')
        order_by = s.validated_data.get('order_by')
        lang = request.LANGUAGE_CODE

        # entity search allows for a reduced filter set, so we check this before calling
        # the actual get_search_results function handling the rest
        allowed = [
            'fulltext',
            'date',
            'daterange',
            'keyword',
            'activity_type',
            'activity',
        ]
        for flt in filters:
            if flt['id'] not in allowed:
                raise ParseError(
                    f'{flt["id"]} not in allowed filters for entity search. allowed: {allowed}',
                    400,
                )

        queryset = ShowroomObject.active_objects.filter(belongs_to=instance)

        return Response(
            get_search_results(queryset, filters, limit, offset, order_by, lang),
            status=200,
        )

    def get_object_or_404(self, **kwargs):
        pk = kwargs['pk'].split('-')[-1]
        instance = get_object_or_404(self.queryset, pk=pk)
        slug = f'entity-{instance.id}'
        if instance.title:
            slug = f'{slugify(instance.title)}-{instance.id}'
        if kwargs['pk'] != slug:
            raise NotFound
        return instance


def get_rendered_edit_showcase(showcase, include_details=False):
    ret = []
    if showcase:
        for sc_id, sc_type in showcase:
            sc_item = {'id': sc_id, 'type': sc_type}
            if include_details:
                sc_item['details'] = {}
                item = None
                try:
                    item = ShowroomObject.active_objects.get(pk=sc_id)
                except ShowroomObject.DoesNotExist:
                    pass
                if item:
                    sc_item['details'] = ShowcaseSerializer(item).data
            ret.append(sc_item)
    return ret


def parse_boolean_query_param(key, value):
    if value == 'true':
        return True
    elif value == 'false':
        return False
    else:
        raise serializers.ValidationError(
            {key: 'If used, has to be either true or false.'}
        )
