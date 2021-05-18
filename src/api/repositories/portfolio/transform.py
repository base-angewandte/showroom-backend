from django.conf import settings

from . import LANGUAGES, get_altlabel, get_preflabel
from .mapping import map


def transform_data(data, schema):
    mapping = map(schema)
    transformed = {}
    for category, fields in mapping.items():
        transformed[category] = [
            transform_field(field, data) for field in fields if data.get(field)
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
        # TODO: remove this after all (current) field transformations have been implemented
        #       and replace with an Exception / log line / admin mail notification(?)
        if settings.DEBUG and not transformed:
            print('not transformed:', field, data.get(field))
    except KeyError as e:
        raise e

    return transformed


# According to the docs/api/api_v1_showroom.yml definition in the showroom-frontend repo
# and the docs/showroom-model-classes.drawio diagram in this repo a CommonText item
# (which should be returned by these field transformations) can either be:
#
#   * a string
#   * a list of string
#   * a list of objects like this: {'label':str, 'value':str, 'url':str, 'source':str}
#     where 'label' and 'value' are required
#
# The BaseTextList base UI component can be used as a reference here, as it will
# consume the provided data: https://base-angewandte.github.io/base-ui-components/#basetextlist
#
# The following field transformation functions should therefore always
# return all localised versions of the above, in the format:
# { 'en': CommonText, 'de': CommonText, ... }


def get_artists(data):
    artists = data.get('artists')

    lines = [a['label'] for a in artists]

    transformed = {}
    for lang in LANGUAGES:
        if len(artists) > 1:
            label = get_altlabel('artist', lang=lang)
        else:
            label = get_preflabel('artist', lang=lang)
        transformed[lang] = {
            'label': label.capitalize(),
            'data': lines,
        }

    return transformed


def get_contributors(data):
    contributors = data.get('contributors')
    lines = [c['label'] for c in contributors]

    transformed = {}
    for lang in LANGUAGES:
        if len(contributors) > 1:
            label = get_altlabel('contributor', lang=lang)
        else:
            label = get_preflabel('contributor', lang=lang)
        transformed[lang] = {
            'label': label.capitalize(),
            'data': lines,
        }

    return transformed


def get_curators(data):
    curators = data.get('curators')
    lines = [c['label'] for c in curators]

    transformed = {}
    for lang in LANGUAGES:
        if len(curators) > 1:
            label = get_altlabel('curator', lang=lang)
        else:
            label = get_preflabel('curator', lang=lang)
        transformed[lang] = {
            'label': label.capitalize(),
            'data': lines,
        }

    return transformed


def get_date_range_time_range_location(data):
    daterange = data.get('date_range_time_range_location')
    line = ''

    """
    The current rational for date_range_time_range_location transformations is as follows:

    * in case of serial events the mapped data from PF to SR shall be displayed the following way:
      - primary field: time-span of the series, plus the first event with date with location
      - secondary field: dates, locations, and location descriptions of every event of the series.
    * in case of single event: put everything into the primary field (except if otherwise noted in the Showroom API Definition spreadsheet)

    Reference: https://basedev.uni-ak.ac.at/redmine/issues/1311
    """

    # in case of several fields, collect all dates and find the min and max dates
    # be aware that any field may or may not be set in any kind of combination
    if len(daterange) > 1:
        dates = []
        for d in daterange:
            date = d.get('date')
            if date:
                date_from = date.get('date_from')
                if date_from:
                    dates.append(date_from)
                date_to = date.get('date_to')
                if date_to:
                    dates.append(date_to)
        dates.sort()
        year_start = dates[0][:4] if dates else None
        year_end = dates[-1][:4] if dates else None
        if year_start:
            line += year_start
            if year_end and year_end != year_start:
                line += f'-{year_end} : '
            else:
                line += ' : '

    # now add the (first) event
    d = daterange[0].get('date')
    if d:
        d_from = d.get('date_from')
        d_to = d.get('date_to')
        if d_from == d_to:
            line += f'{d_from} '
        else:
            line += f'{d_from} - {d_to} '
        # TODO: start and end times are deliberately left out for now, as their semantics is
        #   is not clear (see #1311 for ongoing discussion)

    locations = daterange[0].get('location')
    if locations:
        loc_labels = [loc.get('label') for loc in locations]
        if loc_labels:
            line += ', '.join(loc_labels)
    loc_desc = daterange[0].get('location_description')
    if loc_desc:
        line += f' ({loc_desc})'

    transformed = {}
    for lang in LANGUAGES:
        if len(daterange) > 1:
            label = get_altlabel('date', lang=lang)
        else:
            label = get_preflabel('date', lang=lang)
        transformed[lang] = {
            'label': label.capitalize(),
            'data': line,
        }

    return transformed


def get_organisers(data):
    return data.get('organisers')


def get_url(data):
    return data.get('url')


# def get_(data):
#    return data.get('')
