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
    if not mapping:
        logger.error(f'No mapping is available to transform entry of type: {schema}')
        raise MappingNotFoundError(schema)

    transformed = {}
    for category, fields in mapping.items():
        transformed[category] = []
        for field in fields:
            if type(tf := transform_field(field, data)) == list:
                transformed[category].extend(tf)
            elif tf:
                transformed[category].append(tf)
    return transformed


def transform_field(field, data):
    functions = {
        'artists': get_artists,
        'authors': get_authors,
        'combined_locations': get_combined_locations,
        'contributors': get_contributors,
        'curators': get_curators,
        'date': get_date,
        'date_location': get_date_location,
        'date_location_description': get_date_location_description,
        'date_range_time_range_location': get_date_range_time_range_location,
        'directors': get_directors,
        'documentation_url': get_documentation_url,
        'duration': get_duration,
        'editors': get_editors,
        'git_url': get_git_url,
        'headline': get_headline,
        'isan': get_isan,
        'isbn_doi': get_isbn_doi,
        'keywords': get_keywords,
        'language': get_language,
        'language_format_material_edition': get_language_format_material_edition,
        'material_format': get_material_format,
        'material_format_dimensions': get_material_format_dimensions,
        'open_source_license': get_open_source_license,
        'organisers': get_organisers,
        'programming_language': get_programming_language,
        'published_in': get_published_in,
        'publisher_place_date': get_publisher_place_date,
        'software_developers': get_software_developers,
        'software_version': get_software_version,
        'texts_with_types': get_texts_with_types,
        'type': get_type,
        'url': get_url,
        'volume_issue_pages': get_volume_issue_pages,
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
# return all localised versions of the above, either as a dict in the format of
#   { 'en': CommonText, 'de': CommonText, ... }
# or as a list of such dicts, if the data has to be transformed into separate CommonText fields
#
# If the transformed data is translation independent the a 'default' language key can be used:
#   { 'default': CommonText }


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


def get_authors(data):
    try:
        authors = data.get('data').get('authors')
    except AttributeError:
        return None
    if not authors:
        return None

    lines = [a['label'] for a in authors]

    transformed = {}
    for lang in LANGUAGES:
        if len(authors) > 1:
            label = get_altlabel('author', lang=lang)
        else:
            label = get_preflabel('author', lang=lang)
        transformed[lang] = {
            'label': label.capitalize(),
            'data': lines,
        }

    return transformed


def get_combined_locations(data):
    transformed = []
    if not (inner_data := data.get('data')):
        return []

    def extract_locations(items):
        l_transformed = []
        for item in items:
            if locations := item.get('location'):
                for location in locations:
                    loc = {
                        'coordinates': location.get('geometry').get('coordinates'),
                        'data': [location.get('label')],
                    }
                    if street := location.get('street'):
                        if hn := location.get('house_number'):
                            street = f'{street} {hn}'
                        loc['data'].append(street)
                    if locality := location.get('locality'):
                        if zip := location.get('postcode'):
                            locality = f'{zip} {locality}'
                        loc['data'].append(locality)
                    if country := location.get('country'):
                        loc['data'].append(country)
                    l_transformed.append(loc)
        return l_transformed

    if dtl_ranges := inner_data.get('date_range_time_range_location'):
        transformed.extend(extract_locations(dtl_ranges))
    if date_locations := inner_data.get('date_location'):
        transformed.extend(extract_locations(date_locations))
    if do_locations := inner_data.get('date_opening_location'):
        transformed.extend(extract_locations(do_locations))
    if locations := inner_data.get('location'):
        transformed.extend(extract_locations([{'location': locations}]))
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


def get_date(data):
    try:
        date = data.get('data').get('date')
    except AttributeError:
        return None
    if not date:
        return None

    transformed = {}
    for lang in LANGUAGES:
        transformed[lang] = {
            'label': get_preflabel('date', lang=lang).capitalize(),
            'data': date,
        }
    return transformed


def get_date_location(data, with_description=False):
    try:
        date_loc = data.get('data').get('date_location')
    except AttributeError:
        return None
    if not date_loc:
        return None

    line = ''
    for dl in date_loc:
        if date := dl.get('date'):
            line += date + ', '
        if locations := dl.get('location'):
            for location in locations:
                if loc_label := location.get('label'):
                    line += loc_label + ', '
        if with_description and (loc_desc := dl.get('location_description')):
            line += loc_desc + ', '
    if line:
        line = line[:-2]  # remove trailing ', '

    transformed = {}
    for lang in LANGUAGES:
        if len(date_loc) > 1:
            label_date = get_altlabel('date', lang=lang)
            label_loc = get_altlabel('location', lang=lang)
        else:
            label_date = get_preflabel('date', lang=lang)
            label_loc = get_preflabel('location', lang=lang)
        transformed[lang] = {
            'label': f'{label_date.capitalize()}, {label_loc.capitalize()}',
            'data': line,
        }

    return transformed


def get_date_location_description(data):
    return get_date_location(data, with_description=True)


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


def get_directors(data):
    try:
        directors = data.get('data').get('directors')
    except AttributeError:
        return None
    if not directors:
        return None

    lines = [d['label'] for d in directors]

    transformed = {}
    for lang in LANGUAGES:
        if len(directors) > 1:
            label = get_altlabel('director', lang=lang)
        else:
            label = get_preflabel('director', lang=lang)
        transformed[lang] = {
            'label': label.capitalize(),
            'data': lines,
        }

    return transformed


def get_documentation_url(data):
    try:
        url = data.get('data').get('documentation_url')
    except AttributeError:
        return None
    if not url:
        return None

    transformed = {
        'default': {
            'label': 'URL',
            'data': [
                {
                    'label': 'www',
                    'value': url,
                    'url': url,
                },
            ],
        },
    }
    return transformed


def get_duration(data):
    try:
        duration = data.get('data').get('duration')
    except AttributeError:
        return None
    if not duration:
        return None

    transformed = {}
    for lang in LANGUAGES:
        label = get_preflabel('duration', lang=lang)
        transformed[lang] = {
            'label': label.capitalize(),
            'data': duration,
        }

    return transformed


def get_editors(data):
    try:
        editors = data.get('data').get('editors')
    except AttributeError:
        return None
    if not editors:
        return None

    lines = [e['label'] for e in editors]

    transformed = {}
    for lang in LANGUAGES:
        if len(editors) > 1:
            label = get_altlabel('editor', lang=lang)
        else:
            label = get_preflabel('editor', lang=lang)
        transformed[lang] = {
            'label': label.capitalize(),
            'data': lines,
        }

    return transformed


def get_git_url(data):
    try:
        url = data.get('data').get('git_url')
    except AttributeError:
        return None
    if not url:
        return None

    transformed = {
        'default': {
            'label': 'URL',
            'data': [
                {
                    'label': 'www',
                    'value': url,
                    'url': url,
                },
            ],
        },
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


def get_isan(data):
    try:
        isan = data.get('data').get('isan')
    except AttributeError:
        return None
    if not isan:
        return None

    transformed = {
        'default': {
            'label': '',
            'data': [
                {
                    'label': 'ISAN',
                    'value': isan,
                },
            ],
        },
    }

    return transformed


def get_isbn_doi(data):
    try:
        isbn = data.get('data').get('isbn')
        doi = data.get('data').get('doi')
    except AttributeError:
        return None
    if not isbn and not doi:
        return None

    transformed = {
        'default': {
            'label': '',
            'data': [],
        },
    }
    if isbn:
        transformed['default']['data'].append(
            {
                'label': 'ISBN',
                'value': isbn,
            }
        )
    if doi:
        transformed['default']['data'].append(
            {
                'label': 'DOI',
                'value': doi,
                'url': f'https://dx.doi.org/{doi}',
            }
        )

    return transformed


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


def get_language(data):
    try:
        languages = data.get('data').get('language')
    except AttributeError:
        return None
    if not languages:
        return None

    transformed = {}
    for lang in LANGUAGES:
        transformed[lang] = {
            'label': '',
            'data': '',
        }
        for language in languages:
            transformed[lang]['data'] += f'{language["label"].get(lang)}, '
        # remove the trailing ', '
        transformed[lang]['data'] = transformed[lang]['data'][:-2]

    return transformed


def get_language_format_material_edition(data):
    try:
        languages = data.get('data').get('language')
        formats = data.get('data').get('format')
        materials = data.get('data').get('material')
        edition = data.get('data').get('edition')
    except AttributeError:
        return None
    if not languages and not formats and not materials and not edition:
        return None

    transformed = {}
    for lang in LANGUAGES:
        transformed[lang] = {
            'label': '',
            'data': '',
        }
        if languages:
            for language in languages:
                transformed[lang]['data'] += f'{language["label"].get(lang)}, '
        if formats:
            for format_ in formats:
                transformed[lang]['data'] += f'{format_["label"].get(lang)}, '
        if materials:
            for material in materials:
                transformed[lang]['data'] += f'{material["label"].get(lang)}, '
        if edition:
            transformed[lang]['data'] += f'{edition}'
        else:
            # remove the trailing ", "
            transformed[lang]['data'] = transformed[lang]['data'][:-2]

    return transformed


def get_material_format(data, with_dimensions=False):
    try:
        formats = data.get('data').get('format')
        materials = data.get('data').get('material')
        dimensions = data.get('data').get('dimensions')
    except AttributeError:
        return None
    if not formats and not materials and not dimensions:
        return None

    transformed = {}
    for lang in LANGUAGES:
        transformed[lang] = {
            'label': '',
            'data': '',
        }
        if materials:
            for material in materials:
                transformed[lang]['data'] += f'{material["label"].get(lang)}, '
        if formats:
            for format_ in formats:
                transformed[lang]['data'] += f'{format_["label"].get(lang)}, '
        if with_dimensions and dimensions:
            transformed[lang]['data'] += f'{dimensions}'
        else:
            # remove the trailing ", "
            transformed[lang]['data'] = transformed[lang]['data'][:-2]

    return transformed


def get_material_format_dimensions(data):
    return get_material_format(data, with_dimensions=True)


def get_open_source_license(data):
    try:
        sw_license = data.get('data').get('open_source_license')
    except AttributeError:
        return None
    if not sw_license:
        return None

    transformed = {}
    for lang in LANGUAGES:
        transformed[lang] = {
            'label': get_preflabel('open_source_license', lang=lang).capitalize(),
            'data': sw_license,
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


def get_programming_language(data):
    try:
        p_lang = data.get('data').get('programming_language')
    except AttributeError:
        return None
    if not p_lang:
        return None

    transformed = {}
    for lang in LANGUAGES:
        transformed[lang] = {
            'label': get_preflabel('programming_language', lang=lang).capitalize(),
            'data': p_lang,
        }
    return transformed


def get_published_in(data):
    try:
        published_in = data.get('data').get('published_in')
        date = data.get('data').get('date')
    except AttributeError:
        return None
    if not published_in:
        return None

    if type(published_in) == str:
        transformed = {}
        for lang in LANGUAGES:
            label = get_preflabel('published_in', lang=lang)
            transformed[lang] = {
                'label': label.capitalize(),
                'data': published_in,
            }
    else:
        transformed = []
        for pub in published_in:
            t = {}
            for lang in LANGUAGES:
                label = get_preflabel('published_in', lang=lang)
                line = ''
                if editors := pub.get('editor'):
                    eds = [ed.get('label') for ed in editors]
                    line += ', '.join(eds) + ': '
                if title := pub.get('title'):
                    line += title + '. '
                if subtitle := pub.get('subtitle'):
                    line += subtitle + '. '
                if publishers := pub.get('publisher'):
                    pubs = [p.get('label') for p in publishers]
                    line += ', '.join(pubs)
                if date:
                    line += '. ' + date

                t[lang] = {
                    'label': label.capitalize(),
                    'data': line,
                }

            transformed.append(t)

    return transformed


def get_publisher_place_date(data):
    if not (inner_data := data.get('data')):
        return None

    line = ''
    if publishers := inner_data.get('publishers'):
        p_list = [p.get('label') for p in publishers]
        line = ', '.join(p_list)

    if locations := inner_data.get('location'):
        l_list = [loc.get('label') for loc in locations]
        line = f'{line}, {", ".join(l_list)}'

    if date := inner_data.get('date'):
        line = f'{line}, {date}'

    transformed = {}
    for lang in LANGUAGES:
        if len(publishers) > 1:
            label = get_altlabel('publisher', lang=lang)
        else:
            label = get_preflabel('publisher', lang=lang)
        transformed[lang] = {
            'label': label.capitalize(),
            'data': line,
        }

    return transformed


def get_software_developers(data):
    try:
        developers = data.get('data').get('software_developers')
    except AttributeError:
        return None
    if not developers:
        return None

    lines = [dev['label'] for dev in developers]

    transformed = {}
    for lang in LANGUAGES:
        if len(developers) > 1:
            label = get_altlabel('software_developer', lang=lang)
        else:
            label = get_preflabel('software_developer', lang=lang)
        transformed[lang] = {
            'label': label.capitalize(),
            'data': lines,
        }

    return transformed


def get_software_version(data):
    try:
        version = data.get('data').get('software_version')
    except AttributeError:
        return None
    if not version:
        return None

    transformed = {}
    for lang in LANGUAGES:
        transformed[lang] = {
            'label': get_preflabel('software_version', lang=lang).capitalize(),
            'data': version,
        }

    return transformed


def get_texts_with_types(data):
    texts = data.get('texts')
    transformed = []
    for text in texts:
        t = {}
        for localised_text in text.get('data'):
            lang = localised_text.get('language').get('source')
            # we want e.g. the 'en' out of 'http://base.uni-ak.ac.at/portfolio/languages/en'
            lang = lang.split('/')[-1]
            t[lang] = localised_text.get('text')
        transformed.append(t)
    return transformed


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
            'data': [
                {
                    'label': 'www',
                    'value': url,
                    'url': url,
                },
            ],
        }

    return transformed


def get_volume_issue_pages(data):
    try:
        volume_issue = data.get('data').get('volume')
        pages = data.get('data').get('pages')
    except AttributeError:
        return None
    if not volume_issue and not pages:
        return None

    transformed = {
        'default': {
            'label': '',
            'data': '',
        }
    }
    if volume_issue:
        transformed['default']['data'] += f'{volume_issue}'
    if volume_issue and pages:
        transformed['default']['data'] += ', '
    if pages:
        transformed['default']['data'] += f'{pages}'

    return transformed


# def get_(data):
#    return data.get('')
