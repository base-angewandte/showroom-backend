from datetime import date
from re import match

from django.core.management.base import BaseCommand, CommandError

from api.repositories.portfolio.search_indexer import get_date_rank
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
        if options['date'] is None:
            day = date.today()
        else:
            if not match(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$', options['date']):
                raise CommandError('This does not look like a valid date')
            try:
                day = date.fromisoformat(options['date'])
            except ValueError as err:
                raise CommandError('This does not look like a valid date') from err

        dates = DateRelevanceIndex.objects.all()

        for d in dates:
            d.rank = get_date_rank(d.date, day)
            d.save()
