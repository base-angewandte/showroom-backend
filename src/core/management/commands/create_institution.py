from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from core.models import ShowroomObject, SourceRepository


class Command(BaseCommand):
    help = 'Create a source repository from which objects can be pushed to showroom'

    def add_arguments(self, parser):
        parser.add_argument(
            'repo_id',
            type=str,
            help='The ID of the institutions source repository',
        )
        parser.add_argument(
            'title',
            type=str,
            help='The title/name of the institution',
        )
        parser.add_argument(
            '-s',
            '--source_repo_object_id',
            type=str,
            help='An option source_repo_object_id. Default: slugfiy(title)',
        )

    def handle(self, *args, **options):
        source_repo_object_id = options['source_repo_object_id']
        if not source_repo_object_id:
            source_repo_object_id = slugify(options['title'])

        try:
            repo = SourceRepository.objects.get(pk=options['repo_id'])
        except SourceRepository.DoesNotExist as err:
            raise CommandError('SourceRepository with this ID does not exist') from err

        entity = ShowroomObject.objects.create(
            type=ShowroomObject.INSTITUTION,
            title=options['title'],
            source_repo=repo,
            source_repo_object_id=source_repo_object_id,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created institution with id: {entity.showroom_id}'
            )
        )
