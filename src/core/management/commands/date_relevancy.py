from datetime import date
from re import match

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core.models import DateRelevanceIndex


class Command(BaseCommand):
    help = 'Calculate the rank of dates in the DateRelevanceIndex'

    def add_arguments(self, parser):
        parser.add_argument(
            '-d',
            '--date',
            type=str,
            help='Reference date in the format YYYY-MM-DD. Defaults to today.',
            required=False,
        )

    def handle(self, *args, **options):
        past_weight = settings.CURRENTNESS_PAST_WEIGHT
        day = None

        if options['date'] is None:
            day = date.today()
        else:
            if not match(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$', options['date']):
                CommandError('This does not look like a valid date')
            day = options['date']

        dates = DateRelevanceIndex.objects.all()

        print(f'past weight: {past_weight}')
        print(f'reference date: {day}')
        print(f'number of entries in index: {len(dates)}')
