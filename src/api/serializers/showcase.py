import logging

from rest_framework import serializers

from core.models import Activity, Album

logger = logging.getLogger(__name__)


def get_serialized_showcase_and_warnings(showcase):
    serialized = []
    warnings = []
    for id, showcase_type in showcase:
        if showcase_type == 'activity':
            try:
                item = Activity.objects.get(pk=id)
            except Activity.DoesNotExist:
                warnings.append(f'Activity {id} does not exist.')
        elif showcase_type == 'album':
            try:
                item = Album.objects.get(pk=id)
            except Album.DoesNotExist:
                warnings.append(f'Album {id} does not exist.')
        else:
            # in case something else was stored, we want to log an error, but
            # continue assembling the showcase output
            logger.error(f'Invalid showcase object: {id}, {showcase_type}')
            continue

        serializer = ShowcaseSerializer(item)
        serialized.append(serializer.data)
    return serialized, warnings


class ShowcaseSerializer(serializers.Serializer):
    id = serializers.CharField(
        help_text='ShortUUID of a showcase object (can either be an activity or album)'
    )
    showcase_type = serializers.ChoiceField(
        choices=['activity', 'album'],
        help_text='Which type ob showcase object this is. Either "activtiy" or "album".',
    )
    title = serializers.CharField(
        help_text='Title of this showcase object',
    )
    subtext = serializers.CharField(
        help_text='Subtitle / subtext of this showcase object',
    )
    media = serializers.JSONField()
    additional = serializers.CharField(
        help_text='Only if showcase_type is activity: additional information',
        required=False,
    )
    type = serializers.CharField(
        help_text='Only if showcase_type is activity: type of activity',
        required=False,
    )
    total = serializers.IntegerField(
        help_text='Only if showcase_type is album: total number of items in the album',
        required=False,
    )

    def to_representation(self, instance):
        ret = {
            'id': instance.id,
            'showcase_type': 'activity' if type(instance) == Activity else 'album',
            'title': instance.title,
            'media': [],
        }
        if type(instance) == Activity:
            ret['subtext'] = '. '.join(instance.subtext)
            ret['additional'] = ''  # TODO: discuss what should actually go here
            ret['type'] = instance.type
            media = instance.media_set.all()
            for m in media:
                if previews := m.specifics.get('previews'):
                    ret['media'].extend(previews)
                    break
        elif type(instance) == Album:
            ret['subtext'] = instance.subtitle
            ret['total'] = instance.activities.count()
        return ret
