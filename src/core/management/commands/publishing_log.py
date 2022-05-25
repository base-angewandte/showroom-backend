import os
import subprocess  # nosec: needed to run zgrep
import time
from re import match

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


def get_logfiles():
    return [
        file
        for file in os.listdir(settings.LOG_DIR)
        if file.startswith('publishing.log')
    ]


def get_files_past_retention():
    rotation = settings.PUBLISHING_LOG_ROTATION_DAYS
    retention = settings.PUBLISHING_LOG_RETENTION
    files_past_retention = []
    threshold = time.time() - (rotation + retention) * 24 * 3600
    for file in get_logfiles():
        path = f'{settings.LOG_DIR}/{file}'
        mtime = os.path.getmtime(path)
        if mtime < threshold:
            files_past_retention.append(file)
    return files_past_retention


def get_compressed_logfiles():
    return [f for f in get_logfiles() if f.endswith('.gz')]


def get_files_to_compress():
    return [
        f for f in get_logfiles() if not f.endswith('.gz') and f != 'publishing.log'
    ]


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
            logfiles = get_logfiles()
            logfiles_count = len(logfiles)
            current_logfile_found = 'publishing.log' in logfiles
            compressed_logfiles_count = len(get_compressed_logfiles())
            uncompressed_count = logfiles_count - compressed_logfiles_count
            if current_logfile_found:
                uncompressed_count -= 1

            self.stdout.write(f'Logfiles: {logfiles_count}')
            if not current_logfile_found:
                self.stdout.write(self.style.WARNING('No current logfile found!'))
            self.stdout.write(f'Compressed logfiles: {compressed_logfiles_count}')
            self.stdout.write(f'Rotated uncompressed logfiles: {uncompressed_count}')

            files_past_retention = get_files_past_retention()
            if files_past_retention:
                self.stdout.write(
                    self.style.WARNING('There are files past the retention date')
                )
                for file in files_past_retention:
                    self.stdout.write(file)
            else:
                self.stdout.write(self.style.SUCCESS('No files past retention date'))

        elif mode == 'compress':
            files = get_files_to_compress()
            files.sort()
            for file in files:
                path = f'{settings.LOG_DIR}/{file}'
                subprocess.run(['gzip', path])  # nosec: only using filenames to gzip
            if files:
                self.stdout.write(f'compressed {len(files)} files')
            else:
                self.stdout.write('no uncompressed rotated log files found')

        elif mode == 'retention':
            files_past_retention = get_files_past_retention()
            for file in files_past_retention:
                path = f'{settings.LOG_DIR}/{file}'
                self.stdout.write(f'removing {path}')
                os.remove(path)
            if not files_past_retention:
                self.stdout.write('No files past retention date to remove')
