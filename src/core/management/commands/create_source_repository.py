from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError

from core.models import SourceRepository


class Command(BaseCommand):
    help = 'Create a source repository from which objects can be pushed to showroom'

    def add_arguments(self, parser):
        parser.add_argument('id', type=str, help='The repository ID (integer)')
        parser.add_argument(
            'api_key',
            type=str,
            help='The key used by the repository to authenticate against showroom.',
        )
        parser.add_argument(
            'label',
            type=str,
            help='The name/label of this institution.',
        )
        parser.add_argument(
            'repo_url',
            type=str,
            help='The repository base url, e.g. https://base.uni-ak.ac.at',
        )
        parser.add_argument(
            '-u',
            '--url',
            type=str,
            help='The URL of the institution (e.g. website). Default: repo-url.',
        )
        parser.add_argument(
            '-i', '--icon_url', type=str, help='The icon URL. Default: None'
        )
        parser.add_argument(
            '-p',
            '--label_repo',
            type=str,
            help='The name/label of this repository. Default: label',
        )

    def handle(self, *args, **options):
        label = options['label']
        label_repo = label
        if options['label_repo']:
            label_repo = options['label_repo']

        url_repo = options['repo_url']
        url_institution = url_repo
        if options['url']:
            url_institution = options['url']

        icon = ''
        if options['icon_url']:
            icon = options['icon_url']

        try:
            sr = SourceRepository.objects.create(
                id=options['id'],
                label_institution=label,
                label_repository=label_repo,
                url_institution=url_institution,
                url_repository=url_repo,
                icon=icon,
                api_key=options['api_key'],
            )
        except IntegrityError as err:
            raise CommandError(
                f'Conflict with existing source repository: {err}'
            ) from err

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created source repository with id: {sr.id}'
            )
        )
