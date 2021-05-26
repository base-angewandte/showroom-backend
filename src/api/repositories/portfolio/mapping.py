mapping = {
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
