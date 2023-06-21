from datetime import timedelta
from importlib import import_module

from django_rq.queues import get_queue
from rq.exceptions import NoSuchJobError
from rq.registry import ScheduledJobRegistry

from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.functional import cached_property

from api.repositories.portfolio import activity_lists, get_schema
from api.repositories.user_preferences.transform import (
    update_entity_from_source_repo_data,
)
from core.validators import (
    validate_entity_list,
    validate_list_ordering,
    validate_showcase,
)
from general.models import AbstractBaseModel, ShortUUIDField
from general.utils import slugify


def get_default_list_ordering():
    return [{'id': c, 'hidden': False} for c in activity_lists.list_collections]


def get_default_entity_secondary_details():
    # TODO: make this dynamic as soon as we have labels in SKOS vocab
    return [
        {
            'de': {'data': '', 'label': 'Biografie'},
            'en': {'data': '', 'label': 'Curriculum Vitae'},
        }
    ]


class ActiveShowroomObjectManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(active=True)


class SourceRepository(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True)
    label_institution = models.CharField(max_length=255)
    label_repository = models.CharField(max_length=255)
    url_institution = models.CharField(max_length=255)
    url_repository = models.CharField(max_length=255)
    icon = models.CharField(max_length=255, blank=True)
    api_key = models.CharField(max_length=255, unique=True)

    class Meta:
        indexes = [
            models.Index(fields=['api_key']),
        ]

    def __str__(self):
        return f'[{self.id}] {self.label_institution} : {self.label_repository}'


class ShowroomObject(AbstractBaseModel):
    ACTIVITY = 'act'
    ALBUM = 'alb'
    PERSON = 'per'
    INSTITUTION = 'ins'
    DEPARTMENT = 'dep'
    TYPE_CHOICES = [
        (ACTIVITY, 'activity'),
        (ALBUM, 'album'),
        (PERSON, 'person'),
        (INSTITUTION, 'institution'),
        (DEPARTMENT, 'department'),
    ]

    id = ShortUUIDField(primary_key=True)
    showroom_id = models.CharField(max_length=255, unique=True, default='')
    title = models.CharField(max_length=255)
    subtext = models.JSONField(blank=True, null=True)
    type = models.CharField(max_length=3, choices=TYPE_CHOICES)
    list = models.JSONField(blank=True, null=True)
    primary_details = models.JSONField(blank=True, null=True)
    secondary_details = models.JSONField(blank=True, null=True)
    locations = models.JSONField(blank=True, null=True)
    # TODO@review: is models.PROTECT the right constraint here?
    #   reasoning: we would not want to accidentally delete all objects of a repo only
    #   because a repo itself is deleted. as repo deletion will be a rare activity we
    #   could make sure that the admins explicitly delete or reassign all objects to
    #   another repo first, before a repo can be deleted
    source_repo = models.ForeignKey(SourceRepository, on_delete=models.PROTECT)
    source_repo_object_id = models.CharField(max_length=255)
    source_repo_owner_id = models.CharField(max_length=255, blank=True, null=True)
    source_repo_data = models.JSONField(default=dict)
    date_synced = models.DateTimeField(editable=False, null=True)

    belongs_to = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True
    )
    relations_to = models.ManyToManyField(
        'self',
        through='Relation',
        symmetrical=False,
        related_name='relations_from',
        blank=True,
    )

    active = models.BooleanField(default=True)

    objects = models.Manager()
    active_objects = ActiveShowroomObjectManager()

    # TODO: add gin indizes for those fields used for full text search
    class Meta:
        indexes = [
            GinIndex(fields=['title']),
            models.Index(fields=['source_repo_object_id']),
        ]
        unique_together = ('source_repo', 'source_repo_object_id')

    def __str__(self):
        label = f'{self.title} (ID: {self.id}, type: {self.type})'
        if not self.active:
            label = f'{label} (deactivated)'
        return label

    def save(self, *args, **kwargs):
        old_instance = None
        if self.id:
            try:
                old_instance = ShowroomObject.objects.get(id=self.id)
            except ShowroomObject.DoesNotExist:
                pass

        super().save(*args, **kwargs)

        # in case the object was just created, we have to generate a new showroom_id
        if old_instance is None:
            self.generate_showroom_id()
            ShowroomObject.objects.filter(id=self.id).update(
                showroom_id=self.showroom_id
            )

        # for updated objects check whether the showroom id has to change
        elif self.title != old_instance.title:
            self.generate_showroom_id()
            ShowroomObject.objects.filter(id=self.id).update(
                showroom_id=self.showroom_id
            )
            if self.showroom_id != old_instance.showroom_id:
                ShowroomObjectHistory.objects.create(
                    showroom_id=old_instance.showroom_id,
                    object=self,
                )

    def generate_showroom_id(self, char_limit=4):
        if self.type in [self.PERSON, self.INSTITUTION, self.DEPARTMENT]:
            # for entities the showroom id should be their slugified name plus the first
            # 4 characters of the id. but we have to check whether a (extremely rare)
            # collision happens with another person of the same name where the id starts
            # with the same characters. in that case we increase the characters taken
            # from the id, until we find a unique showroom_id
            if char_limit >= len(self.id):
                self.showroom_id = f'{slugify(self.title)}-{self.id}'
            else:
                self.showroom_id = f'{slugify(self.title)}-{self.id[:char_limit]}'
                if (
                    ShowroomObject.objects.filter(showroom_id=self.showroom_id).exists()
                    or ShowroomObjectHistory.objects.filter(
                        showroom_id=self.showroom_id
                    ).exists()
                ):
                    self.generate_showroom_id(char_limit=char_limit + 1)
        else:
            self.showroom_id = self.id

    def get_showcase_date_info(self):
        dates = [f'{d.date}' for d in self.datesearchindex_set.order_by('date')]
        for d in self.daterangesearchindex_set.order_by('date_from'):
            if (
                d.date_from.day == 1
                and d.date_from.month == 1
                and d.date_to.day == 31
                and d.date_to.month == 12
            ):
                d_from_year = d.date_from.year
                d_to_year = d.date_to.year
                if d_from_year == d_to_year:
                    dates.append(f'{d_from_year}')
                else:
                    dates.append(f'{d_from_year} - {d_to_year}')
            else:
                dates.append(f'{d.date_from} - {d.date_to}')
        ret = ', '.join(dates)
        return ret

    def deactivate(self):
        """Deactivate an object instead of deletion, in order to preserve its
        ID."""
        entity_types = (self.PERSON, self.DEPARTMENT, self.INSTITUTION)
        # check if there are any render jobs scheduled in case of an entity and
        # cancel them before updating any data
        if self.type in entity_types:
            job_ids = [
                f'entity_list_render_{self.id}',
                f'entity_render_contributor_activities_{self.id}',
            ]
            queue = get_queue('default')
            registry = ScheduledJobRegistry(queue=queue)
            for job_id in job_ids:
                if job_id in registry:
                    try:
                        registry.remove(job_id, delete_job=True)
                    except NoSuchJobError:
                        pass

        self.active = False
        self.subtext = []
        self.primary_details = []
        # secondary_details will be kept, in case the entity page is activated again
        # similar to list ordering and showcase in the EntityDetail
        if self.type not in entity_types:
            self.secondary_details = []
        self.list = []
        self.locations = []
        self.source_repo_data = {}
        self.belongs_to = None
        self.save()

        if self.type in entity_types:
            self.entitydetail.deactivate()
            ShowroomObject.objects.filter(belongs_to=self).update(belongs_to=None)
            activities = ShowroomObject.active_objects.filter(
                type=ShowroomObject.ACTIVITY,
                related_usernames__contributor_source_id=self.source_repo_object_id,
            )
            for activity in activities:
                activity.unlink_entity(self)
        if self.type == ShowroomObject.ACTIVITY:
            self.related_usernames.all().delete()

        self.relations_to.clear()
        self.relations_from.clear()

        self.textsearchindex_set.all().delete()
        self.datesearchindex_set.all().delete()
        self.daterangesearchindex_set.all().delete()
        self.daterelevanceindex_set.all().delete()

        self.media_set.all().delete()

    def unlink_entity(self, entity):
        for detail_field in [self.primary_details, self.secondary_details, self.list]:
            for common_text in detail_field:
                for lang in common_text:
                    if data := common_text[lang].get('data'):
                        if type(data) is list:
                            for item in data:
                                if type(item) is dict:
                                    if source := item.get('source'):
                                        if source == entity.showroom_id:
                                            item.pop('source')
        self.save()


@receiver(
    post_save,
    sender=ShowroomObject,
    dispatch_uid='post_save_create_object_details',
)
def create_object_details(sender, instance, created, raw, *args, **kwargs):
    if not created or raw:
        return
    if instance.type == ShowroomObject.ACTIVITY:
        ActivityDetail.objects.get_or_create(showroom_object=instance)
    elif instance.type in [
        ShowroomObject.PERSON,
        ShowroomObject.DEPARTMENT,
        ShowroomObject.INSTITUTION,
    ]:
        EntityDetail.objects.get_or_create(showroom_object=instance)
        instance.secondary_details = get_default_entity_secondary_details()
        instance.save()


class ShowroomObjectHistory(models.Model):
    showroom_id = models.CharField(max_length=255, primary_key=True)
    object = models.ForeignKey(ShowroomObject, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True, editable=False)


class EntityDetail(models.Model):
    showroom_object = models.OneToOneField(
        ShowroomObject, on_delete=models.CASCADE, primary_key=True
    )
    expertise = models.JSONField(blank=True, null=True)
    showcase = models.JSONField(blank=True, null=True, validators=[validate_showcase])
    photo = models.URLField(max_length=255, blank=True, null=True)
    # we have to use a redefined list property here, because validation works
    # different than for the more generic lists used in activities
    list = models.JSONField(default=dict, validators=[validate_entity_list])
    list_ordering = models.JSONField(
        blank=False,
        default=get_default_list_ordering,
        validators=[validate_list_ordering],
    )

    @cached_property
    def photo_id(self):
        if self.photo:
            return self.photo.split('/')[-1].split('.')[0]

    def __str__(self):
        label = f'{self.showroom_object.title} (ID: {self.showroom_object.id})'
        if not self.showroom_object.active:
            label = f'{label} (deactivated)'
        return label

    def get_editing_list(self, lang=settings.LANGUAGE_CODE):
        ret = []
        for order in self.list_ordering:
            if (l_id := order.get('id')) in self.list:
                # TODO: handle cases with no or different translation available
                loc_list = dict(self.list[l_id].get(lang))
                loc_list.update(order)
                ret.append(loc_list)
        return ret

    def render_contributor_activities(self):
        activities = ShowroomObject.active_objects.filter(
            related_usernames__contributor_source_id=self.showroom_object.source_repo_object_id
        )
        for activity in activities:
            schema = get_schema(activity.activitydetail.activity_type.get('source'))
            if schema is None:
                schema = '__none__'
            # we have to import the transform module dynamically to not produce a
            # circular import
            transform = import_module('api.repositories.portfolio.transform')
            # now transform the detail fields and store the activity with the new data
            transformed = transform.transform_data(activity.source_repo_data, schema)
            activity.primary_details = transformed.get('primary_details')
            activity.secondary_details = transformed.get('secondary_details')
            activity.list = transformed.get('list')
            activity.save()

    def render_list(self):
        activities = ShowroomObject.active_objects.filter(
            type=ShowroomObject.ACTIVITY,
            belongs_to=self.showroom_object,
            activitydetail__activity_type__isnull=False,
            related_usernames__contributor_source_id=self.showroom_object.source_repo_object_id,
        )
        self.list = activity_lists.render_list_from_activities(
            activities, self.showroom_object.source_repo_object_id
        )
        self.save()

    @staticmethod
    def enqueue_delayed_job(job_id, function, queue='default'):
        queue = get_queue(queue)
        registry = ScheduledJobRegistry(queue=queue)
        # we only want to enqueue a single job if
        # several are scheduled within a short period
        if job_id in registry:
            try:
                registry.remove(job_id, delete_job=True)
            except NoSuchJobError:
                pass
        queue.enqueue_in(
            timedelta(seconds=settings.WORKER_DELAY_ENTITY),
            function,
            job_id=job_id,
        )

    def enqueue_render_contributor_activities_job(self):
        job_id = f'entity_render_contributor_activities_{self.showroom_object.id}'
        self.enqueue_delayed_job(job_id, self.render_contributor_activities)

    def enqueue_list_render_job(self):
        job_id = f'entity_list_render_{self.showroom_object.id}'
        self.enqueue_delayed_job(job_id, self.render_list)

    def enqueue_update_activities_job(self):
        job_id = f'entity_update_activities_{self.showroom_object.id}'
        self.enqueue_delayed_job(job_id, self.update_activities)

    def update_activities(self):
        """Associate all activities belonging to this entry.

        Checks for all activities which have a source_repo_owner_id set
        to this entity's source_repo_entry_id but are not yet associated
        with the entity in Showroom (e.g. because the activities have
        been pushed before the entity was created). Those activities
        will then be updated so their belongs_to key points to the
        current entity. Also a list render job will be scheduled, as
        well as a job creation relations from activities in which this
        entity is mentioned in a significant role.
        """
        # TODO: discuss: should we generally update all activities or check for those
        #       where belongs_to is not yet set?
        activities = ShowroomObject.active_objects.filter(
            type=ShowroomObject.ACTIVITY,
            source_repo_owner_id=self.showroom_object.source_repo_object_id,
            belongs_to=None,
        )
        activities.update(belongs_to=self.showroom_object)

    def update_from_repo_data(self):
        # this functionality is located in the api.repositories.user_preferences module
        # so we could later allow for different backends providing their own
        # transformation function
        update_entity_from_source_repo_data(self.showroom_object)

    def run_updates(self):
        self.update_from_repo_data()
        if self.showroom_object.active:
            self.update_activities()
            self.enqueue_list_render_job()
            self.enqueue_render_contributor_activities_job()

    def deactivate(self):
        """Reset all data, but preserve showcase and list_ordering."""
        self.expertise = None
        self.photo = None
        self.list = {}
        self.save()


class ActivityDetail(models.Model):
    showroom_object = models.OneToOneField(
        ShowroomObject, on_delete=models.CASCADE, primary_key=True
    )
    activity_type = models.JSONField(blank=True, null=True)
    keywords = models.JSONField(blank=True, null=True)
    featured_medium = models.ForeignKey(
        'Media',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='featured_by',
    )

    def __str__(self):
        label = f'{self.showroom_object.title} (ID: {self.showroom_object.id})'
        if not self.showroom_object.active:
            label = f'{label} (deactivated)'
        return label

    def deactivate(self):
        """Reset all data, but preserve the object itself."""
        self.activity_type = None
        self.keywords = None
        self.featured_medium = None
        self.save()


class TextSearchIndex(models.Model):
    id = models.AutoField(primary_key=True)
    showroom_object = models.ForeignKey(ShowroomObject, on_delete=models.CASCADE)
    language = models.CharField(max_length=255)
    text = models.TextField(default='')
    text_vector = SearchVectorField(null=True)

    class Meta:
        indexes = (GinIndex(fields=['text_vector']),)


class DateSearchIndex(models.Model):
    id = models.AutoField(primary_key=True)
    showroom_object = models.ForeignKey(ShowroomObject, on_delete=models.CASCADE)
    date = models.DateField()


class DateRangeSearchIndex(models.Model):
    id = models.AutoField(primary_key=True)
    showroom_object = models.ForeignKey(ShowroomObject, on_delete=models.CASCADE)
    date_from = models.DateField()
    date_to = models.DateField()


class DateRelevanceIndex(models.Model):
    id = models.AutoField(primary_key=True)
    showroom_object = models.ForeignKey(ShowroomObject, on_delete=models.CASCADE)
    date = models.DateField()
    rank = models.IntegerField(default=2147483647)

    def update_rank(self, reference_date):
        # after bulk creates date is a string not a date object, therefore refresh
        if type(self.date) is str:
            self.refresh_from_db()
        rank = (self.date - reference_date).days
        if rank < 0:
            rank = (-rank) * settings.CURRENTNESS_PAST_WEIGHT
        self.rank = rank
        self.save()


class Media(models.Model):
    IMAGE = 'i'
    AUDIO = 'a'
    VIDEO = 'v'
    DOCUMENT = 'd'
    UNDEFINED = 'x'
    MEDIA_TYPE_CHOICES = [
        (IMAGE, 'Image'),
        (AUDIO, 'Audio'),
        (VIDEO, 'Video'),
        (DOCUMENT, 'Document'),
        (UNDEFINED, 'Undefined'),
    ]

    id = ShortUUIDField(primary_key=True)
    type = models.CharField(max_length=1, choices=MEDIA_TYPE_CHOICES)
    file = models.CharField(max_length=350)
    showroom_object = models.ForeignKey(ShowroomObject, on_delete=models.CASCADE)
    # TODO@review: should we limit max_length here to 129 or even to 90?
    #   reasoning: there was a 127 limit defined in old RFCs for type nad subtype;
    #   newer RFCs suggest even a 64 char limit for type and subtype; the longest IANA
    #   registered types are between 80 & 90 characters
    mime_type = models.CharField(max_length=255)
    exif = models.JSONField(blank=True, null=True)
    license = models.JSONField(blank=True, null=True)
    specifics = models.JSONField(blank=True, null=True)
    featured = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=2147483647)
    source_repo_media_id = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        ordering = ['order', '-created']

    def __str__(self):
        f_name = self.file.split('/')[-1]
        return f'[{self.id}] {self.type}: {f_name} (belongs to: {self.showroom_object})'


class Relation(AbstractBaseModel):
    id = models.AutoField(primary_key=True)
    from_object = models.ForeignKey(
        ShowroomObject, related_name='rel_from_set', on_delete=models.CASCADE
    )
    to_object = models.ForeignKey(
        ShowroomObject, related_name='rel_to_set', on_delete=models.CASCADE
    )

    class Meta:
        indexes = [
            models.Index(fields=['from_object']),
            models.Index(fields=['to_object']),
        ]

        unique_together = ('from_object', 'to_object')


class ContributorActivityRelations(AbstractBaseModel):
    id = models.AutoField(primary_key=True)
    contributor_source_id = models.CharField(max_length=255)
    activity = models.ForeignKey(
        ShowroomObject, related_name='related_usernames', on_delete=models.CASCADE
    )

    class Meta:
        indexes = [
            models.Index(fields=['contributor_source_id']),
        ]

        unique_together = ('contributor_source_id', 'activity')
