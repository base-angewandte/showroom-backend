import requests

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Pull user info from User Preferences'

    def add_arguments(self, parser):
        parser.add_argument('usernames', nargs='+', type=str)

    def handle(self, *args, **options):
        if None in [settings.CAS_API_BASE, settings.USER_PREFERENCES_API_KEY]:
            raise CommandError(
                'A User Preferences config parameter is missing in .env! Cannot push anything.'
            )

        # Pull from User Preferences
        if 'usernames' not in options:
            raise CommandError('Please specify at least one username.')

        pulled_users = []
        user_not_pulled = []

        for username in options['usernames']:
            headers = {
                'X-Api-Key': settings.USER_PREFERENCES_API_KEY,
            }
            r = requests.get(
                settings.CAS_API_BASE + 'user-data-agent/' + username, headers=headers
            )

            if r.status_code == 403:
                raise CommandError(f'Authentication failed: {r.text}')

            elif r.status_code == 400:
                user_not_pulled.append(username)
                self.stdout.write(
                    self.style.WARNING(
                        f'User preferences for user {username} could not be pulled: 400: {r.text}'
                    )
                )

            elif r.status_code == 201:
                result = r.json()
                return result
                # Todo :
                #  save as desired & transformed (see: api/repositories/user_preferences/transform) in Entry? In that case, change return
                # catch value and use otherwise?
            else:
                raise CommandError(
                    f'Something unexpected happened: {r.status_code} {r.text}'
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully pulled {len(pulled_users)}.')
        )
        if len(user_not_pulled) > 0:
            self.stdout.write(
                self.style.WARNING(f'Could not pull {len(user_not_pulled)}.')
            )
            self.stdout.write(str(user_not_pulled))
