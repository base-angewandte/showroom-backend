mapping = {
    'architecture': {
        'primary_details': [
            'headline',
            'type',
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
        'list': ['contributors'],
        'locations': ['combined_locations'],
    },
    'audio': {
        'primary_details': [
            'headline',
            'type',
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
            'contributors',
            'published_in',
        ],
        # 'locations': ['combined_locations'],  # TODO: not yet defined in the specs if we need this here
    },
    'concert': {
        'primary_details': [
            'headline',
            'type',
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
        'list': ['contributors'],
        'locations': ['combined_locations'],
    },
    'conference': {
        'primary_details': [
            'headline',
            'type',
            'organisers',
            'date_range_time_range_location',
            'keywords',
            'url',
        ],
        'secondary_details': [
            'texts_with_types',
            'lecturers',
        ],
        'list': ['contributors'],
        'locations': ['combined_locations'],
    },
    'conference_contribution': {
        'primary_details': [
            'headline',
            'type',
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
        'list': ['contributors'],
        'locations': ['combined_locations'],
    },
    'document_publication': {
        'primary_details': [
            'headline',  # consists of title and subtitle
            'type',
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
            'published_in',
            'contributors',
        ],
        # for entries of this type category no location map should be shown
    },
    'exhibition': {
        'primary_details': [
            'headline',
            'type',
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
        'list': ['contributors'],
        'locations': ['combined_locations'],
    },
    'festival': {
        'primary_details': [
            'headline',
            'type',
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
        'list': ['contributors'],
        'locations': ['combined_locations'],
    },
    'film_video': {
        'primary_details': [
            'headline',
            'type',
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
            'contributors',
            'published_in',
        ],
        # 'locations': ['combined_locations'],  # TODO: not yet defined in the specs if we need this here
    },
    'image': {
        'primary_details': [
            'headline',
            'type',
            'artists',
            'date_location',
            'keywords',
            'url',
        ],
        'secondary_details': [
            'texts_with_types',
            'material_format_dimensions',
        ],
        'list': ['contributors'],
        'locations': ['combined_locations'],
    },
    'sculpture': {
        'primary_details': [
            'headline',
            'type',
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
        'list': ['contributors'],
        'locations': ['combined_locations'],
    },
    'software': {
        'primary_details': [
            'headline',
            'type',
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
        'list': ['contributors'],
        # for entries of category software no location map should be shown
    },
    'empty_placeholder': {
        'primary_details': [],
        'secondary_details': [],
        'list': [],
        'locations': ['combined_locations'],
    },
}


def map(schema):
    return mapping.get(schema)
