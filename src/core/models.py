from django.contrib.postgres.fields import JSONField
from django.db import models

from general.models import AbstractBaseModel, ShortUUIDField


class SourceRepository(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True)
    label_institution = models.CharField(max_length=255)
    label_repository = models.CharField(max_length=255)
    url_institution = models.CharField(max_length=255)
    url_repository = models.CharField(max_length=255)
    icon = models.CharField(max_length=255)
    api_key = models.CharField(max_length=255)


class AbstractShowroomObject(AbstractBaseModel):
    id = ShortUUIDField(primary_key=True)
    title = models.CharField(max_length=255)
    list = JSONField(blank=True, null=True)
    primary_details = JSONField(blank=True, null=True)
    secondary_details = JSONField(blank=True, null=True)
    locations = JSONField(blank=True, null=True)
    dates = JSONField(blank=True, null=True)
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
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True)


class Activity(AbstractShowroomObject):
    type = JSONField(blank=True, null=True)
    featured_media = models.ForeignKey(
        'Media', on_delete=models.SET_NULL, null=True, related_name='featured_by'
    )
    # TODO@review: is cascading the right constraint here?
    #   reasoning: if an entity that has activities (which should be a person) is deleted from the DB, all their
    #              activities should be deleted as well
    belongs_to = models.ForeignKey(Entity, on_delete=models.CASCADE)
    parents = models.ManyToManyField('self', symmetrical=False, related_name='children')


class Album(models.Model):
    id = ShortUUIDField(primary_key=True)
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255)
    secondary_details = JSONField(blank=True, null=True)
    # TODO@review: is cascading the right constraint here? see remark in Activity
    belongs_to = models.ForeignKey(Entity, on_delete=models.CASCADE)
    activities = models.ManyToManyField(Activity)


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
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)
