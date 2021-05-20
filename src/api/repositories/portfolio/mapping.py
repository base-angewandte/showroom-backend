mapping = {
    'festival': {
        'primary_details': [
            'headline',  # consists of title and subtitle
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
    },
    'empty_placeholder': {
        'primary_details': [],
        'secondary_details': [],
        'list': [],
    },
}


def map(schema):
    return mapping.get(schema)
