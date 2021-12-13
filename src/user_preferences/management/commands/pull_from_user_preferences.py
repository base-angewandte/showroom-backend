import requests

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext_lazy as _

from core.models import Entity


class Command(BaseCommand):
    help = 'Pull user info from User Preferences'

    def add_arguments(self, parser):
        parser.add_argument(
            'username',
            nargs='+',
            type=str,
            help=_('One or more user IDs/names from the User Preferences service'),
        )

    def handle(self, *args, **options):
        entities = Entity.objects.all()

        if None in [settings.CAS_API_BASE, settings.USER_PREFERENCES_API_KEY]:
            raise CommandError(
                'A User Preferences config parameter is missing in .env! Cannot push anything.'
            )

        # Pull from User Preferences
        if 'username' not in options:
            raise CommandError('Please specify at least one username.')

        pulled_user_preferences = []
        user_preferences_not_pulled = []

        for username in options['username']:
            headers = {
                'X-Api-Key': settings.USER_PREFERENCES_API_KEY,
            }
            r = requests.get(
                settings.CAS_API_BASE + f'user-data-agent/{username}/', headers=headers
            )

            if r.status_code == 403:
                raise CommandError(f'Authentication failed: {r.text}')

            elif r.status_code == 400:
                user_preferences_not_pulled.append(username)
                self.stdout.write(
                    self.style.WARNING(
                        f'User preferences for user {username} could not be pulled: 400: {r.text}'
                    )
                )

            elif r.status_code in [200, 201]:
                result = r.json()

                for entity in entities:
                    if entity.source_repo_entry_id == username:
                        entity.source_repo_data = result
                        pulled_user_preferences.append(result.get('name', username))
                        entity.save()
                    else:
                        user_preferences_not_pulled.append(result.get('name', username))

            else:
                raise CommandError(
                    f'Something unexpected happened: {r.status_code} {r.text}'
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully pulled {len(pulled_user_preferences)}.')
        )
        if len(user_preferences_not_pulled) > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'Could not pull {len(user_preferences_not_pulled)}.'
                )
            )
            self.stdout.write(str(user_preferences_not_pulled))
