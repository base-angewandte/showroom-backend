from __future__ import annotations

import logging

from django.conf import settings

from core.models import ShowroomObject
from general.datetime.utils import (
    format_datetime_range_string,
    format_datetime_string,
    format_time_range_string,
)

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
        'architecture': get_architecture,
        'artists': get_artists,
        'authors': get_authors,
        'award_ceremony_location_description': get_award_ceremony_location_description,
        'award_date': get_award_date,
        'category': get_category,
        'combined_locations': get_combined_locations,
        'composition': get_composition,
        'commissions': get_commissions,
        'conductors': get_conductors,
        'contributors': get_contributors,
        'curators': get_curators,
        'date': get_date,
        'date_location': get_date_location,
        'date_location_description': get_date_location_description,
        'date_opening_location': get_date_opening_location,
        'date_range': get_date_range,
        'date_range_location': get_date_range_location,
        'date_range_time_range_location': get_date_range_time_range_location,
        'date_time_range_location': get_date_time_range_location,
        'design': get_design,
        'dimensions': get_dimensions,
        'directors': get_directors,
        'documentation_url': get_documentation_url,
        'duration': get_duration,
        'editors': get_editors,
        'fellow': get_fellow,
        'format': get_format,
        'funding': get_funding,
        'funding_category': get_funding_category,
        'git_url': get_git_url,
        'granted_by': get_granted_by,
        'headline': get_headline,
        'isan': get_isan,
        'isbn_doi': get_isbn_doi,
        'jury': get_jury,
        'keywords': get_keywords,
        'language': get_language,
        'language_format_material_edition': get_language_format_material_edition,
        'lecturers': get_lecturers,
        'list_contributors': list_contributors,
        'list_published_in': list_published_in,
        'material': get_material,
        'material_format': get_material_format,
        'material_format_dimensions': get_material_format_dimensions,
        'music': get_music,
        'open_source_license': get_open_source_license,
        'opening': get_opening,
        'organisations': get_organisations,
        'organisers': get_organisers,
        'programming_language': get_programming_language,
        'project_lead': get_project_lead,
        'project_partners': get_project_partners,
        'published_in': get_published_in,
        'publisher_place_date': get_publisher_place_date,
        'software_developers': get_software_developers,
        'software_version': get_software_version,
        'status': get_status,
        'texts_with_types': get_texts_with_types,
        'title_of_event': get_title_of_event,
        'type': get_type,
        'url': get_url,
        'volume_issue_pages': get_volume_issue_pages,
        'winners': get_winners,
    }

    field_transformer = functions.get(field)
    # TODO: remove this after all (current) field transformations have been implemented
    #       and replace with an Exception / log line / admin mail notification(?)
    if settings.DEBUG and not field_transformer:
        logger.error(
            f'No transformation function is available for field: {{{field!r}: {data.get(field)!r}}}'
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


def get_architecture(data):
    try:
        architectures = data.get('data').get('architecture')
    except AttributeError:
        return None
    if not architectures:
        return None

    lines = [transform_entity(a) for a in architectures]

    transformed = {}
    for lang in LANGUAGES:
        if len(architectures) > 1:
            label = get_altlabel('architecture', lang=lang)
        else:
            label = get_preflabel('architecture', lang=lang)
        transformed[lang] = {
            'label': label,
            'data': lines,
        }

    return transformed


def get_artists(data):
    try:
        artists = data.get('data').get('artists')
    except AttributeError:
        return None
    if not artists:
        return None

    lines = [transform_entity(a) for a in artists]

    transformed = {}
    for lang in LANGUAGES:
        if len(artists) > 1:
            label = get_altlabel('artist', lang=lang)
        else:
            label = get_preflabel('artist', lang=lang)
        transformed[lang] = {
            'label': label,
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

    lines = [transform_entity(a) for a in authors]

    transformed = {}
    for lang in LANGUAGES:
        if len(authors) > 1:
            label = get_altlabel('author', lang=lang)
        else:
            label = get_preflabel('author', lang=lang)
        transformed[lang] = {
            'label': label,
            'data': lines,
        }

    return transformed


def get_award_ceremony_location_description(data):
    try:
        date_loc = data.get('data').get('date_location')
        award_ceremony = data.get('data').get('award_ceremony')
    except AttributeError:
        return None
    if not date_loc and not award_ceremony:
        return None

    # TODO: discuss: for simplicity now only the first date_location is taken
    #       combined with date and time of the award ceremony. is there a
    #       use case where further date_locations should be taken into account?
    line = ''
    if award_ceremony:
        time = award_ceremony.get('time')
        if date := award_ceremony.get('date'):
            line += date
        if date and time:
            line += ' '
        if time:
            line += time
        line += ', '
    if date_loc:
        dl = date_loc[0]
        if locs := dl.get('location'):
            loc_strings = [loc.get('label') for loc in locs]
            line += ', '.join(loc_strings) + ', '
        if loc_desc := dl.get('location_description'):
            line += loc_desc + ', '
    if line:
        line = line[:-2]  # remove trailing ', '

    transformed = {}
    for lang in LANGUAGES:
        transformed[lang] = {
            'label': get_preflabel('award_ceremony', lang=lang),
            'data': line,
        }

    return transformed


def get_award_date(data):
    # TODO: discuss: should we take the date of the first date_location or all
    #       listed date_location dates combined? or the date of the award_ceremony?
    try:
        date = data.get('data').get('award_ceremony')
    except AttributeError:
        return None
    if not date:
        return None

    if not (date_string := date.get('date')):
        return None

    transformed = {}
    for lang in LANGUAGES:
        transformed[lang] = {
            'label': get_preflabel('date', lang=lang),
            'data': date_string,
        }

    return transformed


def get_category(data):
    try:
        category = data.get('data').get('category')
    except AttributeError:
        return None
    if not category:
        return None

    transformed = {}
    for lang in LANGUAGES:
        transformed[lang] = {
            'label': get_preflabel('category', lang=lang),
            'data': category,
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
                        'data': [location.get('label')],
                    }
                    if geometry := location.get('geometry'):
                        if coordinates := geometry.get('coordinates'):
                            loc['coordinates'] = coordinates
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


def get_commissions(data):
    try:
        commissions = data.get('data').get('commissions')
    except AttributeError:
        return None
    if not commissions:
        return None

    lines = [transform_entity(c) for c in commissions]

    transformed = {}
    for lang in LANGUAGES:
        if len(commissions) > 1:
            label = get_altlabel('commissions_orders_for_works', lang=lang)
        else:
            label = get_preflabel('commissions_orders_for_works', lang=lang)
        transformed[lang] = {
            'label': label,
            'data': lines,
        }

    return transformed


def get_composition(data):
    try:
        composition = data.get('data').get('composition')
    except AttributeError:
        return None
    if not composition:
        return None

    lines = [transform_entity(c) for c in composition]

    transformed = {}
    for lang in LANGUAGES:
        if len(composition) > 1:
            label = get_altlabel('composition', lang=lang)
        else:
            label = get_preflabel('composition', lang=lang)
        transformed[lang] = {
            'label': label,
            'data': lines,
        }

    return transformed


def get_conductors(data):
    try:
        conductors = data.get('data').get('conductors')
    except AttributeError:
        return None
    if not conductors:
        return None

    lines = [transform_entity(c) for c in conductors]

    transformed = {}
    for lang in LANGUAGES:
        if len(conductors) > 1:
            label = get_altlabel('conductor', lang=lang)
        else:
            label = get_preflabel('conductor', lang=lang)
        transformed[lang] = {
            'label': label,
            'data': lines,
        }

    return transformed


def get_contributors(data, with_roles=True):
    try:
        contributors = data.get('data').get('contributors')
    except AttributeError:
        return None
    if not contributors:
        return None

    if not with_roles:
        lines = [transform_entity(c) for c in contributors]

    transformed = {}
    for lang in LANGUAGES:
        if len(contributors) > 1:
            label = get_altlabel('contributor', lang=lang)
        else:
            label = get_preflabel('contributor', lang=lang)

        if with_roles:
            lines = []
            for contributor in contributors:
                line = contributor.get('label')
                if roles := contributor.get('roles'):
                    for role in roles:
                        line += f' ({role.get("label").get(lang)})'
                lines.append(line)

        transformed[lang] = {
            'label': label,
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

    lines = [transform_entity(c) for c in curators]

    transformed = {}
    for lang in LANGUAGES:
        if len(curators) > 1:
            label = get_altlabel('curator', lang=lang)
        else:
            label = get_preflabel('curator', lang=lang)
        transformed[lang] = {
            'label': label,
            'data': lines,
        }

    return transformed


def get_localized_line(data):
    """Helper function to get localized line."""
    ret = {lang: '' for lang in LANGUAGES}

    location_string = ''
    if locations := data.get('location'):
        if loc_labels := [loc.get('label') for loc in locations]:
            location_string += ', '.join(loc_labels)
    if loc_desc := data.get('location_description'):
        location_string += f' ({loc_desc})'

    for lang in LANGUAGES:
        line = ''
        if date := data.get('date'):
            if isinstance(date, str):
                line += f'{format_datetime_string(date, lang)}, '
            elif isinstance(date, dict):
                d = date.get('date')
                d_from = date.get('date_from')
                d_to = date.get('date_to')
                t_from = date.get('time_from')
                t_to = date.get('time_to')
                if d:
                    line += f'{format_datetime_string(d, lang)} '
                if d_from or d_to:
                    line += f'{format_datetime_range_string(d_from, d_to, lang)} '
                if t_from or t_to:
                    line += f'{format_time_range_string(t_from, t_to, lang)} '
        if location_string:
            line += location_string
        if line:
            ret[lang] = line.strip(', ')

    return ret


def get_transformed_date_field(data: dict, data_field: str, label: str | list[str]):
    """Helper function to transform date fields.

    The following date fields are supported:

    * date_location
    * date_location_description
    * date_opening_location
    * date_range_location
    * date_range_time_range_location
    * date_time_range_location
    """
    if d := data.get(data_field):
        lines = {lang: [] for lang in LANGUAGES}

        for i in d:
            localized_lines = get_localized_line(i)

            for lang in LANGUAGES:
                if line := localized_lines[lang]:
                    lines[lang].append(line)

        transformed = {}
        for lang in LANGUAGES:
            if len(d) > 1:
                if isinstance(label, list):
                    label_string = ', '.join(
                        [get_altlabel(lbl, lang=lang) for lbl in label]
                    )
                else:
                    label_string = get_altlabel(label, lang=lang)
            else:
                if isinstance(label, list):
                    label_string = ', '.join(
                        [get_preflabel(lbl, lang=lang) for lbl in label]
                    )
                else:
                    label_string = get_preflabel(label, lang=lang)
            transformed[lang] = {
                'label': label_string,
                'data': lines[lang],
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
            'label': get_preflabel('date', lang=lang),
            'data': format_datetime_string(date, lang),
        }
    return transformed


def get_date_location(data):
    if d := data.get('data'):
        return get_transformed_date_field(d, 'date_location', ['date', 'location'])


def get_date_location_description(data):
    return get_date_location(data)


def get_date_opening_location(data):
    if d := data.get('data'):
        return get_transformed_date_field(
            d, 'date_opening_location', ['date', 'location']
        )


def get_date_range(data):
    try:
        daterange = data.get('data').get('date_range')
    except AttributeError:
        return None
    if not daterange:
        return None

    d_from = daterange.get('date_from')
    d_to = daterange.get('date_to')
    if d_from or d_to:
        transformed = {}
        for lang in LANGUAGES:
            transformed[lang] = {
                'label': get_preflabel('duration', lang=lang),
                'data': f'{format_datetime_range_string(d_from, d_to, lang)}',
            }

        return transformed


def get_date_range_location(data):
    if d := data.get('data'):
        return get_transformed_date_field(d, 'date_range_location', 'date')


def get_date_range_time_range_location(data):
    if d := data.get('data'):
        return get_transformed_date_field(d, 'date_range_time_range_location', 'date')


def get_date_time_range_location(data):
    if d := data.get('data'):
        return get_transformed_date_field(
            d, 'date_time_range_location', ['date', 'location']
        )


def get_design(data):
    try:
        designers = data.get('data').get('design')
    except AttributeError:
        return None
    if not designers:
        return None

    lines = [transform_entity(d) for d in designers]

    transformed = {}
    for lang in LANGUAGES:
        if len(designers) > 1:
            label = get_altlabel('design', lang=lang)
        else:
            label = get_preflabel('design', lang=lang)
        transformed[lang] = {
            'label': label,
            'data': lines,
        }

    return transformed


def get_dimensions(data):
    try:
        dimensions = data.get('data').get('dimensions')
    except AttributeError:
        return None
    if not dimensions:
        return None

    transformed = {}
    for lang in LANGUAGES:
        label = get_preflabel('dimensions', lang=lang)
        transformed[lang] = {
            'label': label,
            'data': dimensions,
        }

    return transformed


def get_directors(data):
    try:
        directors = data.get('data').get('directors')
    except AttributeError:
        return None
    if not directors:
        return None

    lines = [transform_entity(d) for d in directors]

    transformed = {}
    for lang in LANGUAGES:
        if len(directors) > 1:
            label = get_altlabel('director', lang=lang)
        else:
            label = get_preflabel('director', lang=lang)
        transformed[lang] = {
            'label': label,
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

    transformed = {}
    for lang in LANGUAGES:
        transformed[lang] = {
            'label': get_preflabel('documentation_url', lang=lang),
            'data': [
                {
                    'value': url,
                    'url': url,
                },
            ],
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
            'label': label,
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

    lines = [transform_entity(e) for e in editors]

    transformed = {}
    for lang in LANGUAGES:
        if len(editors) > 1:
            label = get_altlabel('editor', lang=lang)
        else:
            label = get_preflabel('editor', lang=lang)
        transformed[lang] = {
            'label': label,
            'data': lines,
        }

    return transformed


def get_fellow(data):
    try:
        fellows = data.get('data').get('fellow_scholar')
    except AttributeError:
        return None
    if not fellows:
        return None

    lines = [transform_entity(f) for f in fellows]

    transformed = {}
    for lang in LANGUAGES:
        if len(fellows) > 1:
            label = get_altlabel('fellow_scholar', lang=lang)
        else:
            label = get_preflabel('fellow_scholar', lang=lang)
        transformed[lang] = {
            'label': label,
            'data': lines,
        }

    return transformed


def get_format(data):
    try:
        formats = data.get('data').get('format')
    except AttributeError:
        return None
    if not formats:
        return None

    transformed = {}
    for lang in LANGUAGES:
        if len(formats) > 1:
            label = get_altlabel('format', lang=lang)
        else:
            label = get_preflabel('format', lang=lang)
        transformed[lang] = {
            'label': label,
            'data': '',
        }
        if formats:
            for material in formats:
                transformed[lang]['data'] += f'{material["label"].get(lang)}, '
        if transformed[lang]['data']:
            # remove trailing ', '
            transformed[lang]['data'] = transformed[lang]['data'][:-2]

    return transformed


def get_funding(data):
    try:
        funding = data.get('data').get('funding')
    except AttributeError:
        return None
    if not funding:
        return None

    lines = [transform_entity(f) for f in funding]

    transformed = {}
    for lang in LANGUAGES:
        if len(funding) > 1:
            label = get_altlabel('funding', lang=lang)
        else:
            label = get_preflabel('funding', lang=lang)
        transformed[lang] = {
            'label': label,
            'data': lines,
        }

    return transformed


def get_funding_category(data):
    try:
        funding_category = data.get('data').get('funding_category')
    except AttributeError:
        return None
    if not funding_category:
        return None

    transformed = {}
    for lang in LANGUAGES:
        transformed[lang] = {
            'label': get_preflabel('funding_category', lang=lang),
            'data': funding_category,
        }

    return transformed


def get_git_url(data):
    try:
        url = data.get('data').get('git_url')
    except AttributeError:
        return None
    if not url:
        return None

    transformed = {}
    for lang in LANGUAGES:
        transformed[lang] = {
            'label': get_preflabel('git_url', lang=lang),
            'data': [
                {
                    'value': url,
                    'url': url,
                },
            ],
        }
    return transformed


def get_granted_by(data):
    try:
        granted_by = data.get('data').get('granted_by')
    except AttributeError:
        return None
    if not granted_by:
        return None

    lines = [transform_entity(g) for g in granted_by]

    transformed = {}
    for lang in LANGUAGES:
        if len(granted_by) > 1:
            label = get_altlabel('granted_by', lang=lang)
        else:
            label = get_preflabel('granted_by', lang=lang)
        transformed[lang] = {
            'label': label,
            'data': lines,
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

    transformed = {}
    for lang in LANGUAGES:
        label = get_preflabel('isan', lang=lang)
        transformed[lang] = {
            'label': label,
            'data': isan,
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

    transformed = {}
    for lang in LANGUAGES:
        label_isbn = get_preflabel('isbn', lang=lang)
        label_doi = get_preflabel('doi', lang=lang)
        label = f'{label_isbn}, {label_doi}'
        transformed[lang] = {'label': label, 'data': []}

        if isbn:
            transformed[lang]['data'].append(
                {
                    'label': label_isbn,
                    'value': isbn,
                }
            )
        if doi:
            transformed[lang]['data'].append(
                {
                    'label': label_doi,
                    'value': doi,
                    'url': f'https://dx.doi.org/{doi}',
                }
            )

    return transformed


def get_jury(data):
    try:
        jury = data.get('data').get('jury')
    except AttributeError:
        return None
    if not jury:
        return None

    lines = [transform_entity(j) for j in jury]

    transformed = {}
    for lang in LANGUAGES:
        if len(jury) > 1:
            label = get_altlabel('jury', lang=lang)
        else:
            label = get_preflabel('jury', lang=lang)
        transformed[lang] = {
            'label': label,
            'data': lines,
        }

    return transformed


def get_keywords(data):
    keywords = data.get('keywords')
    if not keywords:
        return None

    transformed = {}
    for lang in LANGUAGES:
        keyword_labels = [
            label for kw in keywords if (label := kw.get('label', {}).get(lang))
        ]
        transformed[lang] = {
            'label': get_preflabel('keywords', lang=lang),
            'data': ', '.join(keyword_labels),
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
        language_labels = [
            ln_label for ln in languages if (ln_label := ln['label'].get(lang))
        ]
        transformed[lang] = {
            'label': get_preflabel('language', lang=lang),
            'data': ', '.join(language_labels),
        }

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
        label_lang = get_preflabel('language', lang=lang)
        label_format = get_preflabel('format', lang=lang)
        label_material = get_preflabel('material', lang=lang)
        label_edition = get_preflabel('edition', lang=lang)
        label = f'{label_lang}, {label_format}, {label_material}, {label_edition}'
        transformed[lang] = {
            'label': label,
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


def get_lecturers(data):
    try:
        lecturers = data.get('data').get('lecturers')
    except AttributeError:
        return None
    if not lecturers:
        return None

    lines = [transform_entity(lec) for lec in lecturers]

    transformed = {}
    for lang in LANGUAGES:
        if len(lecturers) > 1:
            label = get_altlabel('lecturer', lang=lang)
        else:
            label = get_preflabel('lecturer', lang=lang)
        transformed[lang] = {
            'label': label,
            'data': lines,
        }

    return transformed


def get_material(data):
    try:
        materials = data.get('data').get('material')
    except AttributeError:
        return None
    if not materials:
        return None

    transformed = {}
    for lang in LANGUAGES:
        if len(materials) > 1:
            label = get_altlabel('material', lang=lang)
        else:
            label = get_preflabel('material', lang=lang)
        transformed[lang] = {
            'label': label,
            'data': '',
        }
        if materials:
            for material in materials:
                transformed[lang]['data'] += f'{material["label"].get(lang)}, '
        if transformed[lang]['data']:
            # remove trailing ', '
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
        label_material = get_preflabel('material', lang=lang)
        label_format = get_preflabel('format', lang=lang)
        label = f'{label_material}, {label_format}'
        if with_dimensions:
            label_dimensions = get_preflabel('format', lang=lang)
            label += f', {label_dimensions}'
        transformed[lang] = {
            'label': label,
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


def get_music(data):
    try:
        musics = data.get('data').get('music')
    except AttributeError:
        return None
    if not musics:
        return None

    lines = [transform_entity(m) for m in musics]

    transformed = {}
    for lang in LANGUAGES:
        if len(musics) > 1:
            label = get_altlabel('music', lang=lang)
        else:
            label = get_preflabel('music', lang=lang)
        transformed[lang] = {
            'label': label,
            'data': lines,
        }

    return transformed


def get_open_source_license(data):
    try:
        sw_license = data.get('data').get('open_source_license')
    except AttributeError:
        return None
    if not sw_license or type(sw_license) is not dict:
        return None
    license_labels = sw_license.get('label')
    if not license_labels or type(license_labels) is not dict:
        return None

    transformed = {}
    for lang in LANGUAGES:
        transformed[lang] = {
            'label': get_preflabel('open_source_license', lang=lang).title(),
            'data': license_labels.get(lang),
        }
        # if there was no translation we take the english default. if there is none,
        # we omit the whole info, but log a warning
        if not transformed[lang]['data']:
            if default_label := license_labels.get('en'):
                transformed[lang]['data'] = default_label
            else:
                logger.warning(
                    f'No english default available for open source license: {sw_license}'
                )
                return None
    return transformed


def get_opening(data):
    try:
        date_loc = data.get('data').get('date_opening_location')
    except AttributeError:
        return None
    if not date_loc:
        return None

    transformed = []
    for dl in date_loc:
        if opening := dl.get('opening'):
            t = {}
            for lang in LANGUAGES:
                date = opening.get('date')
                time_from = opening.get('time_from')
                time_to = opening.get('time_to')
                time = (
                    '-'.join(filter(None, [time_from, time_to])) if time_from else None
                )
                line = ' '.join(filter(None, [date, time]))
                t[lang] = {
                    'label': get_preflabel('opening', lang=lang),
                    'data': line,
                }
            transformed.append(t)

    return transformed


def get_organisations(data):
    try:
        organisations = data.get('data').get('organisations')
    except AttributeError:
        return None
    if not organisations:
        return None

    lines = [transform_entity(o) for o in organisations]

    transformed = {}
    for lang in LANGUAGES:
        if len(organisations) > 1:
            label = get_altlabel('organisation', lang=lang)
        else:
            label = get_preflabel('organisation', lang=lang)
        transformed[lang] = {
            'label': label,
            'data': lines,
        }

    return transformed


def get_organisers(data):
    try:
        organisers = data.get('data').get('organisers')
    except AttributeError:
        return None
    if not organisers:
        return None

    lines = [transform_entity(o) for o in organisers]

    transformed = {}
    for lang in LANGUAGES:
        if len(organisers) > 1:
            label = get_altlabel('organiser_management', lang=lang)
        else:
            label = get_preflabel('organiser_management', lang=lang)
        transformed[lang] = {
            'label': label,
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
            'label': get_preflabel('programming_language', lang=lang),
            'data': p_lang,
        }
    return transformed


def get_project_lead(data):
    try:
        project_leads = data.get('data').get('project_lead')
    except AttributeError:
        return None
    if not project_leads:
        return None

    lines = [transform_entity(p) for p in project_leads]

    transformed = {}
    for lang in LANGUAGES:
        if len(project_leads) > 1:
            label = get_altlabel('project_lead', lang=lang)
        else:
            label = get_preflabel('project_lead', lang=lang)
        transformed[lang] = {
            'label': label,
            'data': lines,
        }

    return transformed


def get_project_partners(data):
    try:
        project_partners = data.get('data').get('project_partnership')
    except AttributeError:
        return None
    if not project_partners:
        return None

    lines = [transform_entity(p) for p in project_partners]

    transformed = {}
    for lang in LANGUAGES:
        if len(project_partners) > 1:
            label = get_altlabel('project_partnership', lang=lang)
        else:
            label = get_preflabel('project_partnership', lang=lang)
        transformed[lang] = {
            'label': label,
            'data': lines,
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

    if type(published_in) is str:
        transformed = {}
        for lang in LANGUAGES:
            label = get_preflabel('published_in', lang=lang)
            transformed[lang] = {
                'label': label,
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
                    'label': label,
                    'data': line,
                }

            transformed.append(t)

    return transformed


def get_publisher_place_date(data):
    if not (inner_data := data.get('data')):
        return None

    value_parts = []
    if publishers := inner_data.get('publishers'):
        p_list = [p.get('label') for p in publishers]
        value_parts.append(', '.join(p_list))

    if locations := inner_data.get('location'):
        l_list = [loc.get('label') for loc in locations]
        value_parts.append(', '.join(l_list))

    date = inner_data.get('date')

    if not value_parts and not date:
        return None

    transformed = {}
    for lang in LANGUAGES:
        if date:
            value = ', '.join(value_parts + [format_datetime_string(date, lang)])
        else:
            value = ', '.join(value_parts)

        label_parts = []
        if publishers:
            if len(publishers) > 1:
                label_parts.append(get_altlabel('publisher', lang=lang).capitalize())
            else:
                label_parts.append(get_preflabel('publisher', lang=lang).capitalize())
        if locations:
            if len(locations) > 1:
                label_parts.append(get_altlabel('location', lang=lang).capitalize())
            else:
                label_parts.append(get_preflabel('location', lang=lang).capitalize())
        if date:
            label_parts.append(get_preflabel('date', lang=lang).capitalize())
        transformed[lang] = {
            'label': ', '.join(label_parts),
            'data': value,
        }

    return transformed


def get_software_developers(data):
    try:
        developers = data.get('data').get('software_developers')
    except AttributeError:
        return None
    if not developers:
        return None

    lines = [transform_entity(d) for d in developers]

    transformed = {}
    for lang in LANGUAGES:
        if len(developers) > 1:
            label = get_altlabel('software_developer', lang=lang)
        else:
            label = get_preflabel('software_developer', lang=lang)
        transformed[lang] = {
            'label': label,
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
            'label': get_preflabel('software_version', lang=lang),
            'data': version,
        }

    return transformed


def get_status(data):
    try:
        status = data.get('data').get('status')
    except AttributeError:
        return None
    if not status or type(status) is not dict:
        return None
    status_labels = status.get('label')
    if not status_labels or type(status_labels) is not dict:
        return None

    transformed = {}
    for lang in LANGUAGES:
        transformed[lang] = {
            'label': get_preflabel('status', lang=lang).capitalize(),
            'data': status_labels.get(lang),
        }
    return transformed


def get_texts_with_types(data):
    texts = data.get('texts')
    if not texts:
        return None

    transformed = []
    for text in texts:
        t = {}
        text_data = text.get('data')
        if not text_data:
            return None

        for localised_text in text_data:
            lang = localised_text.get('language').get('source')
            # we want e.g. the 'en' out of 'http://base.uni-ak.ac.at/portfolio/languages/en'
            lang = lang.split('/')[-1]

            if text_type := text.get('type'):
                label = text_type['label'][lang]
            else:
                label = get_preflabel('text', lang=lang)

            t[lang] = {
                'label': label,
                'data': localised_text.get('text'),
            }
        transformed.append(t)
    return transformed


def get_title_of_event(data):
    try:
        title = data.get('data').get('title_of_event')
    except AttributeError:
        return None
    if not title:
        return None

    transformed = {}
    for lang in LANGUAGES:
        label = get_preflabel('title_of_event', lang=lang)
        transformed[lang] = {
            'label': label,
            'data': title,
        }

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
                'label': get_preflabel('type', lang=lang),
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

    transformed = {}
    for lang in LANGUAGES:
        label_volume = get_preflabel('volume_issue', lang=lang)
        label_pages = get_preflabel('pages', lang=lang)
        label = f'{label_volume}, {label_pages}'
        transformed[lang] = {
            'label': label,
            'data': '',
        }
        if volume_issue:
            transformed[lang]['data'] += f'{volume_issue}'
        if volume_issue and pages:
            transformed[lang]['data'] += ', '
        if pages:
            transformed[lang]['data'] += f'{pages}'

    return transformed


def get_winners(data):
    try:
        winners = data.get('data').get('winners')
    except AttributeError:
        return None
    if not winners:
        return None

    lines = [transform_entity(w) for w in winners]

    transformed = {}
    for lang in LANGUAGES:
        if len(winners) > 1:
            label = get_altlabel('winner', lang=lang)
        else:
            label = get_preflabel('winner', lang=lang)
        transformed[lang] = {
            'label': label,
            'data': lines,
        }

    return transformed


# def get_(data):
#    return data.get('')


# According to the docs/api/api_v1_showroom.yml definition in the showroom-frontend repo
# and the docs/showroom-model-classes.drawio diagram in this repo a CommonList item
# is composed of:
#
#   * a label
#   * a hidden flag
#   * and a data property which is a list of CommonList and/or CommonListItem
#
# The CommonListItem consists of:
#
#   * a value
#   * and a list of attributes
#
# (There is an additional id for ordering for both of the above in the API spec
#  but this is only used for user editable information updates)
#
# The following list field transformation functions should therefore always
# return all localised versions of the above as a dict in the format of
#   { 'en': CommonList, 'de': CommonList, ... }


def list_contributors(data):
    try:
        contributors = data.get('data').get('contributors')
    except AttributeError:
        return None
    if not contributors:
        return None

    lines = [c['label'] for c in contributors]

    transformed = {}
    for lang in LANGUAGES:
        label = get_altlabel('contributor', lang=lang)

        lines = []
        for contributor in contributors:
            line = transform_entity(contributor)
            if roles := contributor.get('roles'):
                line['attributes'] = [role.get('label').get(lang) for role in roles]
            lines.append(line)

        transformed[lang] = {
            'label': label,
            'data': lines,
        }

    return transformed


def list_published_in(data):
    try:
        published_in = data.get('data').get('published_in')
        date = data.get('data').get('date')
    except AttributeError:
        return None
    if not published_in:
        return None

    if type(published_in) is str:
        transformed = {}
        for lang in LANGUAGES:
            label = get_preflabel('published_in', lang=lang)
            transformed[lang] = {
                'label': label,
                'data': [{'value': published_in, 'attributes': []}],
            }
    else:
        transformed = {}
        for lang in LANGUAGES:
            label = get_preflabel('published_in', lang=lang)
            lines = []
            for pub in published_in:
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
                lines.append({'value': line, 'attributes': []})

            transformed[lang] = {'label': label, 'data': lines}

    return transformed


def transform_entity(entity):
    if source_repo_object_id := entity.get('source'):
        try:
            e = ShowroomObject.active_objects.get(
                source_repo_object_id=source_repo_object_id
            )
            ret = {'value': e.title}
            if e.active:
                ret['source'] = e.showroom_id
            return ret
        except ShowroomObject.DoesNotExist:
            pass
    return {
        'value': entity['label'],
    }
