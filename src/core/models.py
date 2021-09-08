from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import models
from django.db.models import Q

from general.models import AbstractBaseModel, ShortUUIDField


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
    showcase = JSONField(blank=True, null=True)
    photo = models.CharField(max_length=255, blank=True)
    parent_choice_limit = Q(type='I') | Q(type='D')
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to=parent_choice_limit,
    )

    def __str__(self):
        return f'{self.title} (ID: {self.id})'


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
    source_repo_data_text = models.TextField(default='')

    def __str__(self):
        return f'{self.title} (ID: {self.id})'


class ActivitySearch(models.Model):
    id = models.AutoField(primary_key=True)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    language = models.CharField(max_length=255)
    text = models.TextField(default='')
    text_vector = SearchVectorField(null=True)

    class Meta:
        indexes = (GinIndex(fields=['text_vector']),)


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
