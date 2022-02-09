from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import models
from django.db.models import Q

from api.repositories.portfolio import activity_lists
from core.validators import (
    validate_entity_list,
    validate_list_ordering,
    validate_showcase,
)
from general.models import AbstractBaseModel, ShortUUIDField


def get_default_list_ordering():
    return [{'id': c, 'hidden': False} for c in activity_lists.list_collections]


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


class AbstractShowroomObject(AbstractBaseModel):
    id = ShortUUIDField(primary_key=True)
    title = models.CharField(max_length=255)
    subtext = JSONField(blank=True, null=True)
    list = JSONField(blank=True, null=True)
    primary_details = JSONField(blank=True, null=True)
    secondary_details = JSONField(blank=True, null=True)
    locations = JSONField(blank=True, null=True)
    # TODO@review: is models.PROTECT the right constraint here?
    #   reasoning: we would not want to accidentally delete all objects of a repo only because a repo itself is deleted.
    #              as repo deletion will be a rare activity we could make sure that the admins explicitly delete or
    #              reassign all objects to another repo first, before a repo can be deleted
    source_repo = models.ForeignKey(SourceRepository, on_delete=models.PROTECT)
    source_repo_entry_id = models.CharField(max_length=255)

    class Meta:
        abstract = True


class Entity(AbstractShowroomObject):
    PERSON = 'P'
    INSTITUTION = 'I'
    DEPARTMENT = 'D'
    ENTITY_TYPE_CHOICES = [
        (PERSON, 'person'),
        (INSTITUTION, 'institution'),
        (DEPARTMENT, 'department'),
    ]
    type = models.CharField(max_length=1, choices=ENTITY_TYPE_CHOICES)
    expertise = JSONField(blank=True, null=True)
    showcase = JSONField(blank=True, null=True, validators=[validate_showcase])
    photo = models.CharField(max_length=255, blank=True)
    # we have to use a redefined list property here, because validation works
    # different than for the more generic lists used in activities
    list = JSONField(default=dict, validators=[validate_entity_list])
    list_ordering = JSONField(
        blank=False,
        default=get_default_list_ordering,
        validators=[validate_list_ordering],
    )
    parent_choice_limit = Q(type='I') | Q(type='D')
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to=parent_choice_limit,
    )
    source_repo_data = JSONField(blank=True, null=True)

    def __str__(self):
        return f'{self.title} (ID: {self.id})'

    def get_editing_list(self, lang=settings.LANGUAGE_CODE):
        ret = []
        for order in self.list_ordering:
            if (l_id := order.get('id')) in self.list:
                # TODO: handle cases with no or different translation available
                loc_list = dict(self.list[l_id].get(lang))
                loc_list.update(order)
                ret.append(loc_list)
        return ret

    def render_list(self):
        q_filter = None
        for f in activity_lists.get_data_contains_filters(self.source_repo_entry_id):
            if not q_filter:
                q_filter = Q(source_repo_data__data__contains=f)
            else:
                q_filter = q_filter | Q(source_repo_data__data__contains=f)
        activities = Activity.objects.filter(
            belongs_to=self, type__isnull=False
        ).filter(q_filter)
        self.list = activity_lists.render_list_from_activities(
            activities, self.source_repo_entry_id
        )
        self.save()


class Activity(AbstractShowroomObject):
    type = JSONField(blank=True, null=True)
    source_repo_owner_id = models.CharField(max_length=255)
    source_repo_data = JSONField(blank=True, null=True)
    featured_media = models.ForeignKey(
        'Media',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='featured_by',
    )
    # TODO@review: is cascading the right constraint here?
    #   reasoning: if an entity that has activities (which should be a person) is deleted from the DB, all their
    #              activities should be deleted as well
    belongs_to = models.ForeignKey(Entity, on_delete=models.CASCADE, null=True)
    relations_to = models.ManyToManyField(
        'self', symmetrical=False, related_name='relations_from', blank=True
    )
    # the following fields are only needed to be more efficient in search
    keywords = JSONField(blank=True, null=True)
    collection_type = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f'{self.title} (ID: {self.id})'

    def get_showcase_date_info(self):
        dates = [f'{d.date}' for d in self.activitysearchdates_set.order_by('date')]
        dates.extend(
            [
                f'{d.date_from} - {d.date_to}'
                for d in self.activitysearchdateranges_set.order_by('date_from')
            ]
        )
        ret = ', '.join(dates)
        return ret


class ActivitySearch(models.Model):
    id = models.AutoField(primary_key=True)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    language = models.CharField(max_length=255)
    text = models.TextField(default='')
    text_vector = SearchVectorField(null=True)

    class Meta:
        indexes = (GinIndex(fields=['text_vector']),)


class ActivitySearchDates(models.Model):
    id = models.AutoField(primary_key=True)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    date = models.DateField()


class ActivitySearchDateRanges(models.Model):
    id = models.AutoField(primary_key=True)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    date_from = models.DateField()
    date_to = models.DateField()


class Album(models.Model):
    id = ShortUUIDField(primary_key=True)
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255)
    secondary_details = JSONField(blank=True, null=True)
    # TODO@review: is cascading the right constraint here? see remark in Activity
    belongs_to = models.ForeignKey(Entity, on_delete=models.CASCADE)
    activities = models.ManyToManyField(Activity)

    def __str__(self):
        return f'{self.title}. {self.subtitle} (ID: {self.id})'


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
    # TODO@review: is cascading the right constraint here?
    #   reasoning: if an activity is deleted all its associated media should also be deleted
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    # TODO@review: should we limit max_length here to 129 or even to 90?
    #   reasoning: there was a 127 limit defined in old RFCs for type nad subtype; newer RFCs suggest even a 64 char
    #              limit for type and subtype; the longest IANA registered types are between 80 & 90 characters
    mime_type = models.CharField(max_length=255)
    exif = JSONField(blank=True, null=True)
    license = JSONField(blank=True, null=True)
    specifics = JSONField(blank=True, null=True)
    source_repo_media_id = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return f'[{self.id}] {self.type}: {self.file}'
