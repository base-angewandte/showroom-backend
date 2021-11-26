import logging

from django.conf import settings
from django.utils.text import slugify

from core.models import Activity, Album

from . import get_schema
from .mapping import map_search

logger = logging.getLogger(__name__)


def gather_labels(items):
    if not items:
        return []
    return [item.get('label') for item in items]


def get_search_item(item, lang=settings.LANGUAGES[0][0]):
    search_item = {
        'id': item.id,
        'type': None,
        'title': None,
        'subtitle': None,
        'description': None,
        'alternative_text': [],
        'image_url': None,
        'source_institution': {
            'label': item.source_repo.label_institution,
            'url': item.source_repo.url_institution,
            'icon': item.source_repo.icon,
        },
        'score': 1,  # TODO
    }

    if type(item) == Activity:
        search_item['type'] = 'activity'
    elif type(item) == Album:
        search_item['type'] = 'album'
    else:
        search_item['id'] = slugify(item.title) + '-' + item.id
        # TODO: refactor this (also in entity serializer, to be configurable)
        if item.type == 'P':
            search_item['type'] = 'person'
        elif item.type == 'I':
            search_item['type'] = 'institution'
        elif item.type == 'D':
            search_item['type'] = 'department'

    if type(item) == Activity:
        # featured_media currently cannot be set explicitly in portfolio
        # therefore we just go through all available media and take the first
        # image we can find. if there is no image, we'll look for the first other
        # available option
        alternative_preview = None
        for medium in item.media_set.all():
            if medium.type == 'i':
                thumbnail = medium.specifics.get('thumbnail')
                if not thumbnail:
                    continue
                search_item['image_url'] = thumbnail
                break
            elif not alternative_preview:
                if medium.type == 'v':
                    if cover := medium.specifics.get('cover'):
                        if cover_gif := cover.get('gif'):
                            alternative_preview = cover_gif
                        elif cover_jpg := cover.get('jpg'):
                            alternative_preview = cover_jpg
                else:
                    alternative_preview = medium.specifics.get('thumbnail')
        if not search_item['image_url'] and alternative_preview:
            search_item['image_url'] = alternative_preview
    else:
        search_item['image_url'] = item.photo if item.photo else None

    activity_schema = None
    if type(item) == Activity and item.type:
        activity_schema = get_schema(item.type.get('source'))
    mapping = map_search(search_item['type'], activity_schema)

    functions = {
        'activity_type_university': get_activity_type_university,
        'architecture_contributors': get_architecture_contributors,
        'artists_contributors': get_artists_contributors,
        'artists_curators_contributors': get_artists_curators_contributors,
        'authors_artists_contributors': get_authors_artists_contributors,
        'authors_editors': get_authors_editors,
        'contributors': get_contributors,
        'design_contributors': get_design_contributors,
        'developers_contributors': get_developers_contributors,
        'directors_contributors': get_directors_contributors,
        'fellow_scholar_funding': get_fellow_scholar_funding,
        'lecturers_contributors': get_lecturers_contributors,
        'music_conductors_composition_contributors': get_music_conductors_composition_contributors,
        'name': get_name,
        'organisers_artists_curators': get_organisers_artists_curators,
        'organisers_lecturers_contributors': get_organisers_lecturers_contributors,
        'project_lead_partners_funding': get_project_lead_partners_funding,
        'skills': None,
        'text_keywords': get_text_keywords,
        'title_subtitle': get_title_subtitle,
        'university': get_university,
        'winners_jury_contributors': get_winners_jury_contributors,
    }

    for field, map_function in mapping.items():
        if map_function is None:
            continue
        if (transform_func := functions.get(map_function)) is None:
            if settings.DEBUG:
                # TODO: discuss: do we want this also in prod, or an admin notification?
                logger.error(
                    f'Missing search mapping function: {{"{field}": "{map_function}"}}'
                )
            continue
        transformed = transform_func(item, lang)

        if field == 'alternative_text':
            search_item[field] = transformed
        else:
            search_item[field] = ', '.join(transformed)

    return search_item


def get_architecture_contributors(item, lang):
    ret = []
    ret.extend(gather_labels(item.source_repo_data['data'].get('architecture')))
    ret.extend(gather_labels(item.source_repo_data['data'].get('contributors')))
    return ret


def get_activity_type_university(item, lang):
    ret = []
    if item.type and (type_label := item.type.get('label')):
        ret.append(type_label.get(lang))
    ret.append(item.source_repo.label_institution)
    return ret


def get_artists_contributors(item, lang):
    ret = []
    ret.extend(gather_labels(item.source_repo_data['data'].get('artists')))
    ret.extend(gather_labels(item.source_repo_data['data'].get('contributors')))
    return ret


def get_artists_curators_contributors(item, lang):
    ret = []
    ret.extend(gather_labels(item.source_repo_data['data'].get('artists')))
    ret.extend(gather_labels(item.source_repo_data['data'].get('curators')))
    ret.extend(gather_labels(item.source_repo_data['data'].get('contributors')))
    return ret


def get_authors_artists_contributors(item, lang):
    ret = []
    ret.extend(gather_labels(item.source_repo_data['data'].get('authors')))
    ret.extend(gather_labels(item.source_repo_data['data'].get('artists')))
    ret.extend(gather_labels(item.source_repo_data['data'].get('contributors')))
    return ret


def get_authors_editors(item, lang):
    ret = []
    ret.extend(gather_labels(item.source_repo_data['data'].get('authors')))
    ret.extend(gather_labels(item.source_repo_data['data'].get('editors')))
    return ret


def get_contributors(item, lang):
    ret = []
    ret.extend(gather_labels(item.source_repo_data['data'].get('contributors')))
    return ret


def get_design_contributors(item, lang):
    ret = []
    ret.extend(gather_labels(item.source_repo_data['data'].get('design')))
    ret.extend(gather_labels(item.source_repo_data['data'].get('contributors')))
    return ret


def get_developers_contributors(item, lang):
    ret = []
    ret.extend(gather_labels(item.source_repo_data['data'].get('software_developers')))
    ret.extend(gather_labels(item.source_repo_data['data'].get('contributors')))
    return ret


def get_directors_contributors(item, lang):
    ret = []
    ret.extend(gather_labels(item.source_repo_data['data'].get('directors')))
    ret.extend(gather_labels(item.source_repo_data['data'].get('contributors')))
    return ret


def get_fellow_scholar_funding(item, lang):
    ret = []
    ret.extend(gather_labels(item.source_repo_data['data'].get('fellow_scholar')))
    ret.extend(gather_labels(item.source_repo_data['data'].get('funding')))
    return ret


def get_music_conductors_composition_contributors(item, lang):
    ret = []
    ret.extend(gather_labels(item.source_repo_data['data'].get('music')))
    ret.extend(gather_labels(item.source_repo_data['data'].get('conductors')))
    ret.extend(gather_labels(item.source_repo_data['data'].get('composition')))
    ret.extend(gather_labels(item.source_repo_data['data'].get('contributors')))
    return ret


def get_lecturers_contributors(item, lang):
    ret = []
    ret.extend(gather_labels(item.source_repo_data['data'].get('lecturers')))
    ret.extend(gather_labels(item.source_repo_data['data'].get('contributors')))
    return ret


def get_name(item, lang):
    return [item.title]


def get_organisers_artists_curators(item, lang):
    ret = []
    ret.extend(gather_labels(item.source_repo_data['data'].get('organisers')))
    ret.extend(gather_labels(item.source_repo_data['data'].get('artists')))
    ret.extend(gather_labels(item.source_repo_data['data'].get('curators')))
    return ret


def get_organisers_lecturers_contributors(item, lang):
    ret = []
    ret.extend(gather_labels(item.source_repo_data['data'].get('organisers')))
    ret.extend(gather_labels(item.source_repo_data['data'].get('lecturers')))
    ret.extend(gather_labels(item.source_repo_data['data'].get('contributors')))
    return ret


def get_project_lead_partners_funding(item, lang):
    ret = []
    ret.extend(gather_labels(item.source_repo_data['data'].get('project_lead')))
    ret.extend(gather_labels(item.source_repo_data['data'].get('project_partnership')))
    ret.extend(gather_labels(item.source_repo_data['data'].get('funding')))
    return ret


def get_text_keywords(item, lang):
    ret = []
    if texts := item.source_repo_data.get('texts'):
        # TODO: do we want to prepend the texts with the text type?
        # TODO: add character limit on overall text lenghts
        for text in texts:
            for section in text['data']:
                if section['language']['source'].split('/')[-1] == lang:
                    ret.append(section['text'])
    if keywords := item.source_repo_data.get('keywords'):
        line = 'Keywords: '  # TODO: replace with localised preflabel
        line += ', '.join([keyword['label'].get(lang) for keyword in keywords])
        ret.append(line)
    return ret


def get_title_subtitle(item, lang):
    ret = [item.title]
    ret.extend(item.subtext)
    return ret


def get_university(item, lang):
    return [item.source_repo.label_institution]


def get_winners_jury_contributors(item, lang):
    ret = []
    ret.extend(gather_labels(item.source_repo_data['data'].get('winners')))
    ret.extend(gather_labels(item.source_repo_data['data'].get('jury')))
    ret.extend(gather_labels(item.source_repo_data['data'].get('contributors')))
    return ret
