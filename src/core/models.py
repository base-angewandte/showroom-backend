from datetime import timedelta

from django_rq.queues import get_queue
from rq.registry import ScheduledJobRegistry

from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver

from api.repositories.portfolio import activity_lists
from api.repositories.user_preferences.transform import (
    update_entity_from_source_repo_data,
)
from core.validators import (
    validate_entity_list,
    validate_list_ordering,
    validate_showcase,
)
from general.models import AbstractBaseModel, ShortUUIDField


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


class SourceRepository(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True)
    label_institution = models.CharField(max_length=255)
    label_repository = models.CharField(max_length=255)
    url_institution = models.CharField(max_length=255)
    url_repository = models.CharField(max_length=255)
    icon = models.CharField(max_length=255, blank=True)
    api_key = models.CharField(max_length=255, unique=True)

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
        'self', symmetrical=False, related_name='relations_from', blank=True
    )

    # TODO: add gin indizes for those fields used for full text search

    def __str__(self):
        return f'{self.title} (ID: {self.id}, type: {self.type})'

    def get_showcase_date_info(self):
        dates = [f'{d.date}' for d in self.datesearchindex_set.order_by('date')]
        dates.extend(
            [
                f'{d.date_from} - {d.date_to}'
                for d in self.daterangesearchindex_set.order_by('date_from')
            ]
        )
        ret = ', '.join(dates)
        return ret


@receiver(post_save, sender=ShowroomObject)
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


class EntityDetail(models.Model):
    showroom_object = models.OneToOneField(
        ShowroomObject, on_delete=models.CASCADE, primary_key=True
    )
    expertise = models.JSONField(blank=True, null=True)
    showcase = models.JSONField(blank=True, null=True, validators=[validate_showcase])
    photo = models.CharField(max_length=255, blank=True)
    # we have to use a redefined list property here, because validation works
    # different than for the more generic lists used in activities
    list = models.JSONField(default=dict, validators=[validate_entity_list])
    list_ordering = models.JSONField(
        blank=False,
        default=get_default_list_ordering,
        validators=[validate_list_ordering],
    )

    def __str__(self):
        return f'{self.showroom_object.title} (ID: {self.showroom_object.id})'

    def get_editing_list(self, lang=settings.LANGUAGE_CODE):
        ret = []
        for order in self.list_ordering:
            if (l_id := order.get('id')) in self.list:
                # TODO: handle cases with no or different translation available
                loc_list = dict(self.list[l_id].get(lang))
                loc_list.update(order)
                ret.append(loc_list)
        return ret

    def create_relations_from_activities(self):
        filters = activity_lists.get_data_contains_filters(
            self.showroom_object.source_repo_object_id
        )
        q_filter = None
        for f in filters:
            if not q_filter:
                q_filter = Q(source_repo_data__data__contains=f)
            else:
                q_filter = q_filter | Q(source_repo_data__data__contains=f)
        activities = ShowroomObject.objects.filter(
            type=ShowroomObject.ACTIVITY,
            activitydetail__activity_type__isnull=False,
        )
        relations_model = ShowroomObject.relations_to.through
        relations = [
            relations_model(
                from_showroomobject_id=activity.id,
                to_showroomobject_id=self.showroom_object.id,
            )
            for activity in activities
        ]
        relations_model.objects.bulk_create(relations, ignore_conflicts=True)

    def render_list(self):
        filters = activity_lists.get_data_contains_filters(
            self.showroom_object.source_repo_object_id
        )
        q_filter = None
        for f in filters:
            if not q_filter:
                q_filter = Q(source_repo_data__data__contains=f)
            else:
                q_filter = q_filter | Q(source_repo_data__data__contains=f)
        activities = ShowroomObject.objects.filter(
            type=ShowroomObject.ACTIVITY,
            belongs_to=self.showroom_object,
            activitydetail__activity_type__isnull=False,
        ).filter(q_filter)
        self.list = activity_lists.render_list_from_activities(
            activities, self.showroom_object.source_repo_object_id
        )
        self.save()

    def enqueue_create_relations_job(self):
        job_id = f'entity_create_relations_from_activities_{self.showroom_object.id}'
        queue = get_queue('default')
        registry = ScheduledJobRegistry(queue=queue)
        # similar to enqueue_list_render_job we only want to enqueue a single job if
        # several are scheduled within a short period
        if job_id in registry:
            registry.remove(job_id)
        queue.enqueue_in(
            timedelta(seconds=settings.WORKER_DELAY_ENTITY_LIST),
            self.create_relations_from_activities,
            job_id=job_id,
        )

    def enqueue_list_render_job(self):
        job_id = f'entity_list_render_{self.showroom_object.id}'
        queue = get_queue('default')
        registry = ScheduledJobRegistry(queue=queue)
        # in case this job gets scheduled several times before it is being executed
        # (e.g. when several activities are pushed for one entity), we only want
        # one single job scheduled after the last call to this function. so we'll
        # delete an older job if there was already one scheduled, before we schedule
        # a new job
        if job_id in registry:
            registry.remove(job_id)
        queue.enqueue_in(
            timedelta(seconds=settings.WORKER_DELAY_ENTITY_LIST),
            self.render_list,
            job_id=job_id,
        )

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
        activities = ShowroomObject.objects.filter(
            type=ShowroomObject.ACTIVITY,
            source_repo_owner_id=self.showroom_object.source_repo_object_id,
        )
        activities.update(belongs_to=self.showroom_object)
        self.enqueue_list_render_job()
        self.enqueue_create_relations_job()

    def update_from_repo_data(self):
        # this functionality is located in the api.repositories.user_preferences module
        # so we could later allow for different backends providing their own
        # transformation function
        update_entity_from_source_repo_data(self.showroom_object)


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
        return f'{self.showroom_object.title} (ID: {self.showroom_object.id})'


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
    file = models.CharField(max_length=255)
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
