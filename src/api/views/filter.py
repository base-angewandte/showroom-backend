from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, viewsets
from rest_framework.response import Response

from django.conf import settings
from django.core.cache import cache

from api.serializers.filter import FilterSerializer
from core.models import ShowroomObject, SourceRepository

static_entity_filters = [
    {
        'id': 'fulltext',
        'type': 'text',
        'label': {
            'en': 'Text',
            'de': 'Text',
        },
        'hidden': False,
    },
    {
        'id': 'date',
        'type': 'date',
        'label': {
            'en': 'Date',
            'de': 'Datum',
        },
        'hidden': False,
    },
    {
        'id': 'daterange',
        'type': 'daterange',
        'label': {
            'en': 'Date Range',
            'de': 'Datumsbereich',
        },
        'hidden': False,
    },
]

static_filters = [
    {
        'id': 'activity',
        'type': 'chips',
        'freetext_allowed': True,
        'label': {
            'en': 'Activities',
            'de': 'Aktivitäten',
        },
        'hidden': False,
    },
    {
        'id': 'person',
        'type': 'chips',
        'freetext_allowed': True,
        'label': {
            'en': 'Persons',
            'de': 'Personen',
        },
        'hidden': False,
    },
    # {
    #     'id': 'locations',
    #     'type': 'chips',
    #     'freetext_allowed': True,
    #     'label': {
    #         'en': 'Locations',
    #         'de': 'Orte',
    #     },
    #     'hidden': False,
    # },
    # {
    #     'id': 'albums',
    #     'type': 'chips',
    #     'freetext_allowed': True,
    #     'label': {
    #         'en': 'Albums',
    #         'de': 'Alben',
    #     },
    #     'hidden': False,
    # },
]
static_filters.extend(static_entity_filters)

label_keywords = {
    'en': 'Keywords',
    'de': 'Schlagwörter',
}

label_activity_types = {
    'en': 'Activity types',
    'de': 'Art der Aktivität',
}

label_institutions = {
    'en': 'Institution',
    'de': 'Institution',
}


def get_static_filter_label(filter_id, lang=settings.LANGUAGE_CODE):
    return next(
        (f['label'][lang] for f in static_filters if f['id'] == filter_id), filter_id
    )


def get_dynamic_filters(lang=settings.LANGUAGE_CODE):
    """Returns the filter definitions for keywords and activity type
    searches."""
    cache_key = f'get_dynamic_filters_{lang}'
    ret = cache.get(cache_key)
    if not ret:
        # TODO: add entity keywords to the keywords filter
        activities = ShowroomObject.objects.filter(
            type=ShowroomObject.ACTIVITY
        ).exclude(source_repo_data__keywords=None)
        keywords = set()
        for activity in activities.iterator(chunk_size=500):
            for kw in activity.source_repo_data['keywords']:
                # keywords should be sortable by localised value
                keywords.add((kw['label'][lang], kw['label'][settings.LANGUAGE_CODE]))
        keyword_filter = {
            'id': 'keyword',
            'type': 'chips',
            'label': label_keywords[lang],
            'hidden': False,
            'freetext_allowed': False,
            'options': [{'id': kw[1], 'label': kw[0]} for kw in sorted(keywords)],
        }

        activities = (
            ShowroomObject.objects.filter(type=ShowroomObject.ACTIVITY)
            .exclude(activitydetail__activity_type__isnull=True)
            .exclude(activitydetail__activity_type={})
        )
        types = set()
        for activity in activities.iterator(chunk_size=500):
            typ = activity.activitydetail.activity_type
            types.add((typ['label'][lang], typ['label'][settings.LANGUAGE_CODE]))
        activity_types_filter = {
            'id': 'activity_type',
            'type': 'chips',
            'label': label_activity_types[lang],
            'hidden': False,
            'freetext_allowed': False,
            'options': [{'id': typ[1], 'label': typ[0]} for typ in sorted(types)],
        }

        institutions = SourceRepository.objects.all()
        institution_filter = {
            'id': 'institution',
            'type': 'chips',
            'label': label_institutions[lang],
            'hidden': True,
            'freetext_allowed': False,
            'options': [
                {'id': i.id, 'label': i.label_institution} for i in institutions
            ],
        }

        # this one is not strictly speaking a dynamic filter, but we have it here, to
        # render the option labels dynamically based on the request language
        showroom_type_filter = {
            'id': 'showroom_type',
            'type': 'chips',
            'freetext_allowed': False,
            'label': 'Showroom type' if lang == 'en' else 'Showroom-Typ',
            'hidden': False,
            'options': [
                {
                    'id': ShowroomObject.ACTIVITY,
                    'label': 'Activity' if lang == 'en' else 'Aktivität',
                },
                {'id': ShowroomObject.PERSON, 'label': 'Person'},
                # TODO: add department, institution, album, once they are fully implemented
            ],
        }

        ret = [
            keyword_filter,
            activity_types_filter,
            showroom_type_filter,
            institution_filter,
        ]
        cache.set(cache_key, ret, 60 * 30)
    return ret


def get_dynamic_entity_filters(entity, lang=settings.LANGUAGE_CODE):
    """Returns the filter definitions for keywords and activity type searches
    on the entity search endpoint."""
    # TODO: cache the dynamic filters for 30 min
    activities = ShowroomObject.objects.filter(
        belongs_to=entity,
        type=ShowroomObject.ACTIVITY,
    ).exclude(source_repo_data__keywords=None)
    keywords = set()
    for activity in activities:
        for kw in activity.source_repo_data['keywords']:
            # keywords should be sortable by localised value
            keywords.add((kw['label'][lang], kw['label'][settings.LANGUAGE_CODE]))
    keyword_filter = {
        'id': 'keyword',
        'type': 'chips',
        'label': label_keywords[lang],
        'hidden': False,
        'freetext_allowed': False,
        'options': [{'id': kw[1], 'label': kw[0]} for kw in sorted(keywords)],
    }

    activities = (
        ShowroomObject.objects.filter(
            belongs_to=entity,
            type=ShowroomObject.ACTIVITY,
        )
        .exclude(activitydetail__activity_type__isnull=True)
        .exclude(activitydetail__activity_type={})
    )
    types = set()
    for activity in activities:
        typ = activity.activitydetail.activity_type
        types.add((typ['label'][lang], typ['label'][settings.LANGUAGE_CODE]))
    activity_types_filter = {
        'id': 'activity_type',
        'type': 'chips',
        'label': label_activity_types[lang],
        'hidden': False,
        'freetext_allowed': False,
        'options': [{'id': typ[1], 'label': typ[0]} for typ in sorted(types)],
    }

    return [keyword_filter, activity_types_filter]


class FilterViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Get all the available filters that can be used in search and
    autocomplete."""

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
    def list(self, request, *args, **kwargs):
        lang = request.LANGUAGE_CODE
        if lang not in [ln[0] for ln in settings.LANGUAGES]:
            lang = settings.LANGUAGE_CODE

        filters = [
            {
                key: (value if key != 'label' else value[lang])
                for key, value in _filter.items()
            }
            for _filter in static_filters
        ]
        filters.extend(get_dynamic_filters(lang=lang))
        return Response(filters, status=200)
