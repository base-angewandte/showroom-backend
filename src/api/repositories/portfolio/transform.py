from django.conf import settings

from .mapping import map


def transform_data(data, schema):
    mapping = map(schema)
    print(mapping)
    transformed = {}
    for category, fields in mapping.items():
        transformed[category] = [
            transform_field(field, data) for field in fields if field
        ]
    return transformed


def transform_field(field, data):
    functions = {
        'artists': get_artists,
        'contributors': get_contributors,
        'curators': get_curators,
        'date_range_time_range_location': get_date_range_time_range_location,
        'organisers': get_organisers,
        'url': get_url,
    }
    try:
        transformed = functions[field](data)
        # TODO: remove this after debugging
        if settings.DEBUG and not transformed:
            print('not transformed:', field, data.get(field))
    except KeyError as e:
        raise e

    return transformed


def get_artists(data):
    return data.get('artists')


def get_contributors(data):
    return data.get('contributors')


def get_curators(data):
    return data.get('curators')


def get_date_range_time_range_location(data):
    return data.get('date_range_time_range_location')


def get_organisers(data):
    return data.get('organisers')


def get_url(data):
    return data.get('url')


# def get_(data):
#    return data.get('')
