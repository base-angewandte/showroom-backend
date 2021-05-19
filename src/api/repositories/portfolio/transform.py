import logging

from django.conf import settings

from . import (
    LANGUAGES,
    FieldTransformerMissingError,
    MappingNotFoundError,
    get_altlabel,
    get_preflabel,
)
from .mapping import map

logger = logging.getLogger(__name__)


def transform_data(data, schema):
    mapping = map(schema)
    print(data)
    if not mapping:
        logger.error(f'No mapping is available to transform entry of type: {schema}')
        raise MappingNotFoundError(schema)

    transformed = {}
    for category, fields in mapping.items():
        transformed[category] = [transform_field(field, data) for field in fields]
    print(transformed)
    return transformed


def transform_field(field, data):
    functions = {
        'artists': get_artists,
        'contributors': get_contributors,
        'curators': get_curators,
        'date_range_time_range_location': get_date_range_time_range_location,
        'headline': get_headline,
        'keywords': get_keywords,
        'organisers': get_organisers,
        'texts_with_types': get_texts_with_types,
        'type': get_type,
        'url': get_url,
    }

    field_transformer = functions.get(field)
    # TODO: remove this after all (current) field transformations have been implemented
    #       and replace with an Exception / log line / admin mail notification(?)
    if settings.DEBUG and not field_transformer:
        logger.error(
            f'No transformation function is available for field: {{"{field}": "{data.get(field)}"}}'
        )
        raise FieldTransformerMissingError(field)

    transformed = functions[field](data)
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
    try:
        artists = data.get('data').get('artists')
    except AttributeError:
        return None
    if not artists:
        return None

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
    try:
        contributors = data.get('data').get('contributors')
    except AttributeError:
        return None
    if not contributors:
        return None

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
    try:
        curators = data.get('data').get('curators')
    except AttributeError:
        return None
    if not curators:
        return None

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
    try:
        daterange = data.get('data').get('date_range_time_range_location')
    except AttributeError:
        return None
    if not daterange:
        return None

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


def get_headline(data):
    title = data.get('title')
    subtitle = data.get('subtitle')
    if not title and not subtitle:
        return None

    headline = title + '. ' if title else ''
    if subtitle:
        headline += subtitle

    # the headline is the same in all languages, therefore only using a default key
    return {
        'default': {
            'label': headline,
        }
    }


def get_keywords(data):
    keywords = data.get('keywords')
    if not keywords:
        return None

    transformed = {}
    for lang in LANGUAGES:
        keyword_labels = [
            label for kw in keywords if (label := kw.get('label').get(lang))
        ]
        transformed[lang] = {
            'label': '',
            'data': {
                'label': get_preflabel('keywords', lang=lang),
                'value': ', '.join(keyword_labels),
            },
        }

    return transformed


def get_organisers(data):
    try:
        organisers = data.get('data').get('organisers')
    except AttributeError:
        return None
    if not organisers:
        return None

    lines = [c['label'] for c in organisers]

    transformed = {}
    for lang in LANGUAGES:
        if len(organisers) > 1:
            label = get_altlabel('organiser_management', lang=lang)
        else:
            label = get_preflabel('organiser_management', lang=lang)
        transformed[lang] = {
            'label': label.capitalize(),
            'data': lines,
        }

    return transformed


def get_texts_with_types(data):
    print('TODO: text_with_types')  # TODO
    return None


def get_type(data):
    typ = data.get('type')
    if not typ:
        return None

    transformed = {}
    for lang in LANGUAGES:
        label = typ.get('label').get(lang)
        if label:
            transformed[lang] = {
                'label': '',
                'data': label,
            }

    return transformed


def get_url(data):
    try:
        url = data.get('data').get('url')
    except AttributeError:
        return None
    if not url:
        return None

    transformed = {}
    for lang in LANGUAGES:
        transformed[lang] = {
            'label': 'URL',
            'data': {
                'label': 'www',
                'value': url,
                'url': url,
            },
        }
    return transformed


# def get_(data):
#    return data.get('')
