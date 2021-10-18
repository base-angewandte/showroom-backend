import logging

from django.conf import settings

from core.models import ActivitySearch

from . import get_schema
from .mapping import map_indexer

logger = logging.getLogger(__name__)


def index_activity(activity):
    data = activity.source_repo_data

    indexed = {}
    for (lang, _lang_label) in settings.LANGUAGES:
        indexed[lang] = []
        if title := data.get('title'):
            indexed[lang].append(title)
        if subtitle := data.get('subtitle'):
            indexed[lang].append(subtitle)
        if texts := data.get('texts'):
            for text in texts:
                for text_data in text.get('data'):
                    ln = text_data['language']['source'].split('/')[-1]
                    if ln == lang:
                        indexed[lang].append(text_data.get('text'))

    # TODO: should type and keywords be added here as well?

    # Now run type/category-specific indexing functions, in case the data key is set
    if (inner_data := data.get('data')) and type(inner_data) == dict:
        if entry_type := activity.source_repo_data.get('type'):
            if collection := get_schema(entry_type.get('source')):
                indexers = map_indexer(collection)

                for indexer in indexers:
                    indexer_result = get_index(indexer, inner_data)
                    for (lang, _lang_label) in settings.LANGUAGES:
                        if res := indexer_result.get(lang):
                            indexed[lang].append(res)

    for lang, values in indexed.items():
        try:
            search_index = ActivitySearch.objects.get(activity=activity, language=lang)
        except ActivitySearch.DoesNotExist:
            search_index = False

        if not search_index:
            ActivitySearch.objects.create(
                activity=activity, language=lang, text='; '.join(values)
            )
        else:
            search_index.text = '; '.join(values)
            search_index.save()


def get_index(indexer, data):
    function_map = {
        'contributors': get_contributors,
        'documentation_url': get_documentation_url,
        'license': get_license,
        'programming_language': get_programming_language,
        'software_developers': get_software_developers,
    }

    indexer_fn = function_map.get(indexer)
    if settings.DEBUG and not indexer_fn:
        logger.error(f'No indexer function is available for field: {indexer}')
    return indexer_fn(data) if indexer_fn else {}


def get_contributors(data):
    contributors = data.get('contributors')
    if contributors and type(contributors) == list:
        text_index = ', '.join([c.get('label') for c in contributors])
    else:
        return {}
    return {lang: text_index for (lang, _lang_label) in settings.LANGUAGES}


def get_documentation_url(data):
    url = data.get('documentation_url')
    return {lang: url for (lang, _lang_label) in settings.LANGUAGES}


def get_license(data):
    license = data.get('open_source_license')
    if type(license) is not dict:
        return {}
    label = license.get('label')
    if type(label) is not dict:
        return {}
    return {lang: label.get(lang) for (lang, _lang_label) in settings.LANGUAGES}


def get_programming_language(data):
    prog_lang = data.get('programming_language')
    return {lang: prog_lang for (lang, _lang_label) in settings.LANGUAGES}


def get_software_developers(data):
    devs = data.get('software_developers')
    if devs and type(devs) == list:
        text_index = ', '.join([d.get('label') for d in devs])
    else:
        return {}
    return {lang: text_index for (lang, _lang_label) in settings.LANGUAGES}
