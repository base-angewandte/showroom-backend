from skosmos_client import SkosmosClient

from django.conf import settings
from django.core.cache import cache

CACHE_TIME = 86400  # 1 day

skosmos = SkosmosClient(api_base=settings.SKOSMOS_API)

ACTIVE_TUPLES = []


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


init()
