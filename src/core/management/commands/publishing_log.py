import os
import subprocess  # nosec: needed to run zgrep
from re import match

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'View and maintain the publishing log'

    def add_arguments(self, parser):
        parser.add_argument(
            '-m',
            '--mode',
            type=str,
            help='Mode of operation. See docs for details.',
            choices=['stats', 'view', 'compress', 'retention'],
            default='stats',
        )
        parser.add_argument(
            '-a',
            '--activity-id',
            type=str,
            help='ID of the activity to print publishing info for if -m view is used',
            required=False,
        )

    def handle(self, *args, **options):
        mode = options['mode']
        if not mode:
            mode = 'stats'

        if mode == 'view':
            activity = options['activity_id']
            if not activity:
                raise CommandError('You have to provide an activity ID for view mode.')
            if len(activity) != 22 or not match(r'^[0-9a-zA-Z]{22}$', activity):
                raise CommandError('This does not look like a valid ShortUUID.')
            # to output all publishing info from oldest to newest, we'll do some
            # sorting of the rotated logs first and append the current log at the end
            files = [
                file
                for file in os.listdir(settings.LOG_DIR)
                if file.startswith('publishing.log') and file != 'publishing.log'
            ]
            files.sort()
            files.append('publishing.log')

            # now walk through all files and grep for the activity. also keep track
            # if nothing at all is found
            activity_found = False
            for file in files:
                cmd = ['zgrep', activity, f'{settings.LOG_DIR}/{file}']
                process = subprocess.run(cmd, capture_output=True, text=True)  # nosec:
                # ... we've properly validated all options to the command
                if process.stdout:
                    activity_found = True
                    self.stdout.write(self.style.SUCCESS(f'{file}:'))
                    self.stdout.write(str(process.stdout))
            if not activity_found:
                self.stdout.write(f'No publishing activity logged for {activity}.')

        elif mode == 'stats':
            print('not yet implemented')  # TODO

        elif mode == 'compress':
            print('not yet implemented')  # TODO

        elif mode == 'retention':
            print('not yet implemented')  # TODO
