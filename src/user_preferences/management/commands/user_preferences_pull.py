from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext_lazy as _

from api.repositories.user_preferences import sync


class Command(BaseCommand):
    help = 'Pull user info from User Preferences'

    def add_arguments(self, parser):
        parser.add_argument(
            'username',
            nargs='+',
            type=str,
            help=_('One or more user IDs from the User Preferences service'),
        )

    def handle(self, *args, **options):

        if None in [
            settings.USER_PREFERENCES_API_BASE,
            settings.USER_PREFERENCES_API_KEY,
        ]:
            raise CommandError(
                'A User Preferences config parameter is missing in .env! Cannot push anything.'
            )

        # Pull from User Preferences
        if 'username' not in options:
            raise CommandError('Please specify at least one username.')

        sucessfully_pulled = []
        not_pulled = []

        for username in options['username']:
            result = sync.pull_user_data(username)
            if result:
                sucessfully_pulled.append(result.get('name', username))
            else:
                not_pulled.append(username)

        self.stdout.write(
            self.style.SUCCESS(f'Successfully pulled {len(sucessfully_pulled)} users.')
        )
        if not_pulled:
            self.stdout.write(
                self.style.WARNING(
                    f'Could not pull {len(not_pulled)} users: {", ".join(not_pulled)}'
                )
            )
