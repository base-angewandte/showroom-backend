import datetime
import logging
import re

from django.conf import settings

from core.models import (
    DateRangeSearchIndex,
    DateRelevanceIndex,
    DateSearchIndex,
    TextSearchIndex,
)

from . import get_schema
from .mapping import map_indexer
from .utils import role_fields

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
                if type(text) is dict:
                    text_data = text.get('data')
                    if type(text_data) is not list:
                        continue
                    for text_data in text.get('data'):
                        ln = text_data['language']['source'].split('/')[-1]
                        if ln == lang:
                            indexed[lang].append(text_data.get('text'))

    # Add type and keywords to activity
    if (activity_type := data.get('type')) and type(activity_type) is dict:
        if (label := activity_type.get('label')) and type(label) is dict:
            for (lang, _lang_label) in settings.LANGUAGES:
                if text := label.get(lang):
                    indexed[lang].append(text)

    if (keywords := data.get('keywords')) and type(keywords) is list:
        for kw in keywords:
            if type(kw) is not dict:
                continue
            if (label := kw.get('label')) and type(label) is dict:
                for (lang, _lang_label) in settings.LANGUAGES:
                    if text := label.get(lang):
                        indexed[lang].append(text)

    # Now run type/category-specific indexing functions, in case the data key is set
    if (inner_data := data.get('data')) and type(inner_data) == dict:
        # Index all role-based fields for names/labels
        contributors = get_contributors(inner_data)
        if contributors:
            for lang in contributors:
                indexed[lang].append(contributors[lang])
        # Index all other inner data based on defined mapping
        if entry_type := activity.source_repo_data.get('type'):
            if collection := get_schema(entry_type.get('source')):
                indexers = map_indexer(collection)

                for indexer in indexers:
                    indexer_result = get_index(indexer, inner_data)
                    for (lang, _lang_label) in settings.LANGUAGES:
                        if res := indexer_result.get(lang):
                            indexed[lang].append(res)

    for lang, values in indexed.items():
        search_index, created = TextSearchIndex.objects.get_or_create(
            showroom_object=activity, language=lang
        )
        search_index.text = '; '.join(values)
        search_index.save()

    # now do the date related indexing
    if inner_data and type(inner_data) == dict:
        dates = []
        date_ranges = []
        # collect all possible dates and date locations
        if date := inner_data.get('date'):
            append_date(date, dates, date_ranges)
        if award_ceremony := inner_data.get('award_ceremony'):
            if date := award_ceremony.get('date'):
                append_date(date, dates, date_ranges)
        if d := inner_data.get('date_location'):
            for dl in d:
                if date := dl.get('date'):
                    append_date(date, dates, date_ranges)
        if d := inner_data.get('date_location_description'):
            for dl in d:
                if date := dl.get('date'):
                    append_date(date, dates, date_ranges)
        if d := inner_data.get('date_opening_location'):
            for dl in d:
                if date := dl.get('date'):
                    append_date_range(date, dates, date_ranges)
                if opening := dl.get('opening'):
                    if date := opening.get('date'):
                        append_date(date, dates, date_ranges)
        if date := inner_data.get('date_range'):
            append_date_range(date, dates, date_ranges)
        if d := inner_data.get('date_range_location'):
            for dl in d:
                if date := dl.get('date'):
                    append_date_range(date, dates, date_ranges)
        if d := inner_data.get('date_range_time_range_location'):
            for dl in d:
                if date := dl.get('date'):
                    append_date_range(date, dates, date_ranges)
        if d := inner_data.get('date_time_range_location'):
            for dl in d:
                if date := dl.get('date'):
                    append_date(date.get('date'), dates, date_ranges)
        # clear all old search index values for this activity
        DateSearchIndex.objects.filter(showroom_object=activity).delete()
        DateRangeSearchIndex.objects.filter(showroom_object=activity).delete()
        DateRelevanceIndex.objects.filter(showroom_object=activity).delete()
        # store the collected dates and date ranges as new search index values
        DateSearchIndex.objects.bulk_create(
            [DateSearchIndex(showroom_object=activity, date=date) for date in dates]
        )
        DateRangeSearchIndex.objects.bulk_create(
            [
                DateRangeSearchIndex(
                    showroom_object=activity, date_from=dr[0], date_to=dr[1]
                )
                for dr in date_ranges
            ]
        )
        dates.extend([dr[0] for dr in date_ranges])
        dates.extend([dr[1] for dr in date_ranges])
        inserted = DateRelevanceIndex.objects.bulk_create(
            [DateRelevanceIndex(showroom_object=activity, date=d) for d in dates]
        )
        today = datetime.date.today()
        for dr in inserted:
            dr.update_rank(today)


def index_entity(entity):
    indexed = {}
    for (lang, _lang_label) in settings.LANGUAGES:
        indexed[lang] = []

    # index keywords
    if entity.entitydetail.expertise and type(entity.entitydetail.expertise) == dict:
        for lang in entity.entitydetail.expertise.keys():
            indexed[lang].extend(entity.entitydetail.expertise[lang])

    # now flatten the indexed item to a string and store them on the index table
    for lang, values in indexed.items():
        search_index, created = TextSearchIndex.objects.get_or_create(
            showroom_object=entity, language=lang
        )
        search_index.text = '; '.join(values)
        search_index.save()


def append_date(date, dates, date_ranges):
    if re.match(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$', date):
        dates.append(date)
    elif re.match(r'^[0-9]{4}$', date):
        date_ranges.append((f'{date}-01-01', f'{date}-12-31'))


def append_date_range(date_range, dates, date_ranges):
    date_from = date_range.get('date_from')
    date_to = date_range.get('date_to')
    if date_from and date_to:
        if re.match(r'^[0-9]{4}$', date_from):
            date_from = f'{date_from}-01-01'
        if re.match(r'^[0-9]{4}$', date_to):
            date_to = f'{date_to}-12-31'
        date_ranges.append((date_from, date_to))
    elif date_from:
        append_date(date_from, dates, date_ranges)
    elif date_to:
        append_date(date_to, dates, date_ranges)


def get_index(indexer, data):
    simple_labels = [
        'category',
        'documentation_url',
        'doi',
        'funding_category',
        'git_url',
        'isan',
        'isbn',
        'programming_language',
        'software_version',
        'title_of_event',
        'url',
    ]
    function_map = {
        'format': get_format,
        'language': get_language,
        'material': get_material,
        'published_in': get_published_in,
        'open_source_license': get_open_source_license,
    }

    if indexer in simple_labels:
        indexed = get_simple_label(data, indexer)
    else:
        indexer_fn = function_map.get(indexer)
        if settings.DEBUG and not indexer_fn:
            logger.error(f'No indexer function is available for field: {indexer}')
        indexed = indexer_fn(data) if indexer_fn else {}
    return indexed


def get_contributors(data):
    labels = []
    for role in role_fields:
        if role_data := data.get(role):
            if type(role_data) == list:
                for r in role_data:
                    if type(r) == dict and 'label' in r:
                        labels.append(r.get('label'))
    if labels:
        text_index = ', '.join(labels)
        return {lang: text_index for (lang, _lang_label) in settings.LANGUAGES}
    return {}


def get_format(data):
    return get_vocabulary_list_labels(data, 'format')


def get_language(data):
    return get_vocabulary_list_labels(data, 'language')


def get_material(data):
    return get_vocabulary_list_labels(data, 'material')


def get_open_source_license(data):
    os_license = data.get('open_source_license')
    if type(os_license) is not dict:
        return {}
    label = os_license.get('label')
    if type(label) is not dict:
        return {}
    return {lang: label.get(lang) for (lang, _lang_label) in settings.LANGUAGES}


def get_published_in(data):
    indexed = {}
    labels = []
    published_in = data.get('published_in')
    if type(published_in) is str:
        labels.append(published_in)
    elif type(published_in) is list:
        for pub in published_in:
            if type(pub) is not dict:
                continue
            if title := pub.get('title'):
                labels.append(title)
            if subtitle := pub.get('subtitle'):
                labels.append(subtitle)
            for role in ['editor', 'publisher']:
                if contributors := pub.get(role):
                    if type(contributors) is not list:
                        continue
                    for contributor in contributors:
                        if type(contributor) is not dict:
                            continue
                        if 'label' in contributor and type(contributor['label']) is str:
                            labels.append(contributor['label'])
    if labels:
        text_index = ', '.join(labels)
        indexed = {lang: text_index for (lang, _lang_label) in settings.LANGUAGES}
    return indexed


def get_simple_label(data, indexing_item):
    if label := data.get(indexing_item):
        return {lang: label for (lang, _lang_label) in settings.LANGUAGES}
    return {}


def get_software_developers(data):
    devs = data.get('software_developers')
    if devs and type(devs) == list:
        text_index = ', '.join([d.get('label') for d in devs])
    else:
        return {}
    return {lang: text_index for (lang, _lang_label) in settings.LANGUAGES}


def get_vocabulary_list_labels(data, field):
    indexed = {}
    if item_list := data.get(field):
        if type(item_list) is not list:
            return indexed
        for item in item_list:
            if type(item) is not dict:
                continue
            if 'label' in item and type(item['label']) == dict:
                for lang in item['label']:
                    if lang not in indexed:
                        indexed[lang] = []
                    indexed[lang].append(item['label'][lang])
    if indexed:
        for lang in indexed:
            indexed[lang] = ', '.join(indexed[lang])
    return indexed
