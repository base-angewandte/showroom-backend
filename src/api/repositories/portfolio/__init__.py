from rdflib import SKOS
from requests import RequestException
from skosmos_client import SkosmosClient

from django.conf import settings
from django.core.cache import cache

CACHE_TIME = 86400  # 1 day

skosmos = SkosmosClient(api_base=settings.SKOSMOS_API)

ACTIVE_TUPLES = []

# TODO: use i18n similar to portfolio
LANGUAGES = ['de', 'en']


def init():
    for schema in settings.ACTIVE_SCHEMAS:
        members = get_collection_members(
            f'http://base.uni-ak.ac.at/portfolio/taxonomy/collection_{schema}'
        )
        ACTIVE_TUPLES.append((members, schema))


def get_collection_members(collection, maxhits=1000, use_cache=True):
    cache_key = f'get_collection_members_{collection}'

    members = cache.get(cache_key) if use_cache else None
    if not members:
        m = skosmos.search(query='*', group=collection, maxhits=maxhits, lang='en')
        members = [i['uri'] for i in m]

        if members:
            cache.set(cache_key, members, CACHE_TIME)

    return members or []


def get_schema(entry_type):
    for types, schema in ACTIVE_TUPLES:
        if entry_type in types:
            return schema


def get_altlabel(concept, project=settings.VOC_ID, graph=settings.VOC_GRAPH, lang=None):
    # TODO: use i18n similar to portfolio
    language = lang or 'en'
    cache_key = f'get_altlabel_{language}_{concept}'

    label = cache.get(cache_key)
    if not label:
        try:
            g = skosmos.data(f'{graph}{concept}')
            for _uri, l in g.subject_objects(SKOS.altLabel):
                if l.language == language:
                    label = l
                    break
        except RequestException:
            pass

    label = label or get_preflabel(concept, project, graph)

    if label:
        cache.set(cache_key, label, CACHE_TIME)

    return label


def get_preflabel(
    concept, project=settings.VOC_ID, graph=settings.VOC_GRAPH, lang=None
):
    # TODO: use i18n similar to portfolio
    language = lang or 'en'
    cache_key = f'get_preflabel_{language}_{concept}'

    label = cache.get(cache_key)
    if not label:
        c = skosmos.get_concept(project, f'{graph}{concept}')
        try:
            label = c.label(language)
        except KeyError:
            try:
                label = c.label('de' if language == 'en' else 'en')
            except KeyError:
                pass
        except RequestException:
            pass

        if label:
            cache.set(cache_key, label, CACHE_TIME)

    return label or ''


init()
