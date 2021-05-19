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
    'empty_placeholder': {
        'primary_details': [],
        'secondary_details': [],
        'list': [],
    },
}


def map(schema):
    return mapping.get(schema)
