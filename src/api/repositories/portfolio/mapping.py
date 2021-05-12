mapping = {
    'festival': {
        'primary_details': [
            'artists',
            'curators',
            'date_range_time_range_location',
            'url',
        ],
        'secondary_details': ['organisers'],
        'list': ['contributors'],
    }
}


def map(schema):
    return mapping.get(schema)
