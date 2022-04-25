import logging

from django.conf import settings
from django.core.cache import cache
from django.utils.text import slugify

from core.models import ShowroomObject

from . import get_schema
from .mapping import map_search

logger = logging.getLogger(__name__)


def gather_labels(items):
    if not items:
        return []
    return [item.get('label') for item in items]


def get_search_item(item, lang=settings.LANGUAGES[0][0]):
    cache_key = f'get_search_item_{item.id}_{lang}'

    search_item = cache.get(cache_key)
    if not search_item:
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
            'score': 0,
        }
        if hasattr(item, 'rank'):
            search_item['score'] = item.rank

        if item.type == ShowroomObject.ACTIVITY:
            search_item['type'] = 'activity'
        elif item.type == ShowroomObject.ALBUM:
            search_item['type'] = 'album'
        else:
            search_item['id'] = slugify(item.title) + '-' + item.id
            # TODO: refactor this (also in entity serializer, to be configurable)
            if item.type == ShowroomObject.PERSON:
                search_item['type'] = 'person'
            elif item.type == ShowroomObject.INSTITUTION:
                search_item['type'] = 'institution'
            elif item.type == ShowroomObject.DEPARTMENT:
                search_item['type'] = 'department'

        if item.type == ShowroomObject.ACTIVITY:
            # in case a featured medium is set, we'll use this. if non is set explicitly
            # we search if there is any image attached to the entry and take this one.
            media = item.media_set.all()
            featured_medium = media.filter(featured=True)
            if featured_medium:
                medium = featured_medium[0]
                if medium.type == 'v':
                    if cover := medium.specifics.get('cover'):
                        search_item['image_url'] = cover.get('jpg')
                else:
                    search_item['image_url'] = medium.specifics.get('thumbnail')
            if search_item['image_url'] is None:
                alternative_preview = None
                for medium in media:
                    if medium.type == 'i':
                        thumbnail = medium.specifics.get('thumbnail')
                        if not thumbnail:
                            continue
                        search_item['image_url'] = thumbnail
                        break
                    elif not alternative_preview:
                        if medium.type == 'v':
                            if cover := medium.specifics.get('cover'):
                                if cover_jpg := cover.get('jpg'):
                                    alternative_preview = cover_jpg
                        else:
                            alternative_preview = medium.specifics.get('thumbnail')
                if not search_item['image_url'] and alternative_preview:
                    search_item['image_url'] = alternative_preview
        elif item.type in [
            ShowroomObject.PERSON,
            ShowroomObject.DEPARTMENT,
            ShowroomObject.INSTITUTION,
        ]:
            photo = item.entitydetail.photo
            search_item['image_url'] = photo if photo else None

        activity_schema = None
        if (
            item.type == ShowroomObject.ACTIVITY
            and item.activitydetail
            and item.activitydetail.activity_type
        ):
            activity_schema = get_schema(
                item.activitydetail.activity_type.get('source')
            )
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
            'skills': get_skills,
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
            # TODO: discuss: should we actually just filter out None values or should
            #       we try to get a default value instead, if the localised is not available?
            transformed = [item for item in transformed if item]

            if field == 'alternative_text':
                search_item[field] = transformed
            else:
                search_item[field] = ', '.join(transformed)
        cache.set(cache_key, search_item, 60 * 5)

    return search_item


def get_architecture_contributors(item, lang):
    ret = []
    ret.extend(gather_labels(item.source_repo_data['data'].get('architecture')))
    ret.extend(gather_labels(item.source_repo_data['data'].get('contributors')))
    return ret


def get_activity_type_university(item, lang):
    ret = []
    if item.type == ShowroomObject.ACTIVITY:
        typ = item.activitydetail.activity_type
        if typ and (type_label := typ.get('label')):
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


def get_skills(item, lang):
    ret = []
    if hasattr(item, 'entitydetail') and type(item.entitydetail) == dict:
        items = item.entitydetail.expertise.get(lang)
        if type(items) == list:
            ret.extend(items)
    return ret


def get_text_keywords(item, lang):
    ret = []
    if texts := item.source_repo_data.get('texts'):
        # TODO: do we want to prepend the texts with the text type?
        # TODO: add character limit on overall text lenghts
        for text in texts:
            if text.get('data') is None:
                continue
            for section in text['data']:
                if section['language']['source'].split('/')[-1] == lang:
                    ret.append(section['text'])
    if keywords := item.source_repo_data.get('keywords'):
        line = 'Keywords: '  # TODO: replace with localised preflabel
        kw_labels = [keyword['label'].get(lang) for keyword in keywords]
        # TODO: discuss: should we actually just filter out None values or should
        #       we try to get a default value instead, if the localised is not available?
        kw_labels = [item for item in kw_labels if item]
        line += ', '.join(kw_labels)
        ret.append(line)
    return ret


def get_title_subtitle(item, lang):
    ret = [item.title]
    if type(item.subtext) is list:
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
