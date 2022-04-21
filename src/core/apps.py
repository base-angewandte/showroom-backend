import django_rq

from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'core'

    scheduler = django_rq.get_scheduler('high')

    jobs = [
        {
            'id': 'get_dynamic_filters_de',
            'schedule': '*/25 * * * *',
            'function': 'api.views.filter.get_dynamic_filters',
            'kwargs': {
                'lang': 'de',
                'use_cache': False,
            },
        },
        {
            'id': 'get_dynamic_filters_en',
            'schedule': '*/25 * * * *',
            'function': 'api.views.filter.get_dynamic_filters',
            'kwargs': {
                'lang': 'en',
                'use_cache': False,
            },
        },
    ]

    for job in jobs:
        if job['id'] not in scheduler:
            scheduler.cron(
                job['schedule'],
                job['function'],
                id=job['id'],
                timeout=7200,
                kwargs=job['kwargs'],
            )
