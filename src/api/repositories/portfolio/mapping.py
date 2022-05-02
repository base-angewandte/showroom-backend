import logging

from django.conf import settings

logger = logging.getLogger(__name__)


mapping = {
    '__none__': {
        'primary_details': [
            'keywords',
        ],
        'secondary_details': [
            'texts_with_types',
        ],
        'list': [],
    },
    'architecture': {
        'primary_details': [
            'architecture',
            'date_location_description',
            'keywords',
            'url',
        ],
        'secondary_details': [
            'texts_with_types',
            'material_format',
            'dimensions',
        ],
        'list': ['list_contributors'],
        'locations': ['combined_locations'],
    },
    'audio': {
        'primary_details': [
            'authors',
            'artists',
            'date_location_description',
            'keywords',
            'url',
        ],
        'secondary_details': [
            'texts_with_types',
            'material_format',
            'duration',
            'language',
        ],
        'list': [
            'list_contributors',
            'list_published_in',
        ],
        # for entries of category audio no location map should be shown
    },
    'awards_and_grants': {
        'primary_details': [
            'winners',
            'granted_by',
            'award_date',
            'keywords',
            'url',
        ],
        'secondary_details': [
            'texts_with_types',
            'category',
            'jury',
            'award_ceremony_location_description',
        ],
        'list': ['list_contributors'],
        # for entries of category awards and grants no location map should be shown
    },
    'concert': {
        'primary_details': [
            'music',
            'composition',
            'date_time_range_location',
            'keywords',
            'url',
        ],
        'secondary_details': [
            'texts_with_types',
            'conductors',
            'opening',
        ],
        'list': ['list_contributors'],
        'locations': ['combined_locations'],
    },
    'conference': {
        'primary_details': [
            'organisers',
            'date_range_time_range_location',
            'keywords',
            'url',
        ],
        'secondary_details': [
            'texts_with_types',
            'lecturers',
        ],
        'list': ['list_contributors'],
        'locations': ['combined_locations'],
    },
    'conference_contribution': {
        'primary_details': [
            'lecturers',
            'date_range_time_range_location',
            'keywords',
            'url',
        ],
        'secondary_details': [
            'texts_with_types',
            'title_of_event',
            'organisers',
        ],
        'list': ['list_contributors'],
        'locations': ['combined_locations'],
    },
    'design': {
        'primary_details': [
            'design',
            'date_location_description',
            'keywords',
            'url',
        ],
        'secondary_details': [
            'commissions',
            'texts_with_types',
            'material_format',
        ],
        'list': ['list_contributors'],
        # for entries of category design no location map should be shown
    },
    'document_publication': {
        'primary_details': [
            'authors',
            'editors',
            'publisher_place_date',
            'keywords',
            'isbn_doi',
            'url',
        ],
        'secondary_details': [
            'texts_with_types',
            'volume_issue_pages',
            'language_format_material_edition',
        ],
        'list': [
            'list_published_in',
            'list_contributors',
        ],
        # for entries of this type category no location map should be shown
    },
    'event': {  # is now labeled "activity", the potax id still collection_event
        'primary_details': [
            'date_range_time_range_location',
            'keywords',
            'url',
        ],
        'secondary_details': ['texts_with_types'],
        'list': ['list_contributors'],
        'locations': ['combined_locations'],
    },
    'exhibition': {
        'primary_details': [
            'artists',
            'curators',
            'date_opening_location',
            'keywords',
            'url',
        ],
        'secondary_details': [
            'texts_with_types',
            'opening',
        ],
        'list': ['list_contributors'],
        'locations': ['combined_locations'],
    },
    'fellowship_visiting_affiliation': {
        'primary_details': [
            'fellow',
            'date_range_location',
            'keywords',
            'url',
        ],
        'secondary_details': [
            'commissions',
            'funding',
            'organisations',
            'texts_with_types',
        ],
        'list': ['list_contributors'],
        'locations': ['combined_locations'],
    },
    'festival': {
        'primary_details': [
            'artists',
            'curators',
            'date_range_time_range_location',
            'keywords',
            'url',
        ],
        'secondary_details': [
            'texts_with_types',
            'organisers',
        ],
        'list': ['list_contributors'],
        'locations': ['combined_locations'],
    },
    'film_video': {
        'primary_details': [
            'directors',
            'date_location_description',
            'keywords',
            'url',
        ],
        'secondary_details': [
            'texts_with_types',
            'isan',
            'material_format',
            'duration',
            'language',
        ],
        'list': [
            'list_contributors',
            'list_published_in',
        ],
        # for entries of category film/video no location map should be shown
    },
    'image': {
        'primary_details': [
            'artists',
            'date_location',
            'keywords',
            'url',
        ],
        'secondary_details': [
            'texts_with_types',
            'material_format_dimensions',
        ],
        'list': ['list_contributors'],
        'locations': ['combined_locations'],
    },
    'performance': {
        'primary_details': [
            'artists',
            'date_range_time_range_location',
            'keywords',
            'url',
        ],
        'secondary_details': [
            'texts_with_types',
            'material',
            'format',
        ],
        'list': ['list_contributors'],
        'locations': ['combined_locations'],
    },
    'research_project': {
        'primary_details': [
            'project_lead',
            'project_partners',
            'date_range',
            'keywords',
            'url',
        ],
        'secondary_details': [
            'texts_with_types',
            'funding',
            'funding_category',
        ],
        'list': ['list_contributors'],
        # for entries of category research project no location map should be shown
    },
    'sculpture': {
        'primary_details': [
            'artists',
            'date_location_description',
            'keywords',
            'url',
        ],
        'secondary_details': [
            'texts_with_types',
            'material_format',
            'dimensions',
        ],
        'list': ['list_contributors'],
        'locations': ['combined_locations'],
    },
    'software': {
        'primary_details': [
            'software_developers',
            'date',
            'open_source_license',
            'keywords',
            'url',
        ],
        'secondary_details': [
            'texts_with_types',
            'programming_language',
            'git_url',
            'documentation_url',
            'software_version',
        ],
        'list': ['list_contributors'],
        # for entries of category software no location map should be shown
    },
}


def map(schema):
    return mapping.get(schema)


search_mapping = {
    'default': {
        'title': 'title_subtitle',
        'subtitle': None,
        'description': 'activity_type_university',
        'alternative_text': 'text_keywords',
    },
    'person': {
        'title': 'name',
        'description': 'university',
        'alternative_text': 'skills',
    },
    'activity': {
        'architecture': {'subtitle': 'architecture_contributors'},
        'audio': {'subtitle': 'authors_artists_contributors'},
        'awards_and_grants': {'subtitle': 'winners_jury_contributors'},
        'concert': {'subtitle': 'music_conductors_composition_contributors'},
        'conference': {'subtitle': 'organisers_lecturers_contributors'},
        'conference_contribution': {'subtitle': 'lecturers_contributors'},
        'design': {'subtitle': 'design_contributors'},
        'document_publication': {'subtitle': 'authors_editors'},
        'event': {'subtitle': 'contributors'},
        'exhibition': {'subtitle': 'artists_curators_contributors'},
        'fellowship_visiting_affiliation': {'subtitle': 'fellow_scholar_funding'},
        'festival': {'subtitle': 'organisers_artists_curators'},
        'film_video': {'subtitle': 'directors_contributors'},
        'image': {'subtitle': 'artists_contributors'},
        'performance': {'subtitle': 'artists_contributors'},
        'research_project': {'subtitle': 'project_lead_partners_funding'},
        'sculpture': {'subtitle': 'artists_contributors'},
        'software': {'subtitle': 'developers_contributors'},
    },
}


def map_search(schema, activity_schema=None):
    mapping = dict(search_mapping['default'])
    if schema == 'activity' and activity_schema:
        if m := search_mapping['activity'].get(activity_schema):
            mapping.update(m)
        else:
            if settings.DEBUG:
                # TODO: discuss: do we want this also in prod, or an admin notification?
                logger.error(
                    f'Missing search mapping for activity_schema: {activity_schema}'
                )

    elif schema != 'activity':
        if m := search_mapping.get(schema):
            mapping.update(m)
    return mapping


indexer_mapping = {
    'default': [
        'award_ceremony',
        'category',
        'doi',
        'format',
        'funding_category',
        'isan',
        'isbn',
        'language',
        'material',
        'published_in',
        'title_of_event',
        'url',
    ],
    # if activities of a specific category should not use all field defined in default,
    # create a specific mapping as the following
    'software': [
        'documentation_url',
        'git_url',
        'open_source_license',
        'software_version',
        'programming_language',
    ],
}


def map_indexer(schema):
    return indexer_mapping.get(schema) or indexer_mapping['default']
