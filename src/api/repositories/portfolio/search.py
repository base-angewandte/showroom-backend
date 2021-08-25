import logging

from django.conf import settings

from core.models import Activity, Album

from . import get_schema
from .mapping import map_search

logger = logging.getLogger(__name__)


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
        # TODO: discuss what frontend really needs here and then create config
        #       setting for this and core.model.Entity type choices
        if item.type == 'P':
            search_item['type'] = 'person'
        elif item.type == 'I':
            search_item['type'] = 'institution'
        elif item.type == 'D':
            search_item['type'] = 'department'

    activity_schema = None
    if type(item) == Activity and item.type:
        activity_schema = get_schema(item.type.get('source'))
    mapping = map_search(search_item['type'], activity_schema)

    functions = {
        'activity_type_university': get_activity_type_university,
        'artists_contributors': get_artists_contributors,
        'author_editors': None,
        'directors_contributors': None,
        'name': get_name,
        'skills': None,
        'text_keywords': get_text_keywords,
        'title_subtitle': get_title_subtitle,
        'university': get_university,
    }

    print(item, search_item['type'], activity_schema)
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
        print('transformed:', transformed)

        if field == 'alternative_text':
            search_item[field] = transformed
        else:
            search_item[field] = ', '.join(transformed)

    return search_item


def get_activity_type_university(item, lang):
    ret = []
    ret.append(item.type['label'].get(lang))
    ret.append(item.source_repo.label_institution)
    return ret


def get_artists_contributors(item, lang):
    ret = []
    if artists := item.source_repo_data['data'].get('artists'):
        ret.extend(artist.get('label') for artist in artists)
    if contributors := item.source_repo_data['data'].get('contributors'):
        ret.extend([contributor.get('label') for contributor in contributors])
    return ret


def get_name(item, lang):
    return [item.title]


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
