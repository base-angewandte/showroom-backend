import logging

from rest_framework import serializers

from core.models import ShowroomObject

logger = logging.getLogger(__name__)


def get_serialized_showcase_and_warnings(showcase):
    serialized = []
    warnings = []
    for id, showcase_type in showcase:
        try:
            item = ShowroomObject.active_objects.get(pk=id)
        except ShowroomObject.DoesNotExist:
            warnings.append(f'{showcase_type} {id} does not exist.')
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
            'showcase_type': 'activity'
            if instance.type == ShowroomObject.ACTIVITY
            else 'album',
            'title': instance.title,
            'previews': [],
        }
        if instance.type == ShowroomObject.ACTIVITY:
            ret['subtext'] = '. '.join(instance.subtext)
            ret['additional'] = instance.get_showcase_date_info()
            ret['type'] = instance.activitydetail.activity_type
            media = instance.media_set.all().order_by('-featured', 'order')
            # in case a featured medium is set, we'll use this, if there is a usable
            # thumbnail or cover image. otherwise we take the first medium according to
            # the given ordering, that has a usable thumbnail or cover image
            alternative_preview = None
            for m in media:
                if previews := m.specifics.get('previews'):
                    ret['previews'].extend(previews)
                    break
                elif not alternative_preview:
                    if m.type == 'v':
                        if cover := m.specifics.get('cover'):
                            if cover_jpg := cover.get('jpg'):
                                alternative_preview = cover_jpg
                                break
                    else:
                        if alternative_preview := m.specifics.get('thumbnail'):
                            break
            if not ret['previews'] and alternative_preview:
                widths = ['640w', '768w', '1024w', '1366w', '1600w', '1632w']
                ret['previews'] = [{w: alternative_preview} for w in widths]
        elif instance.type == ShowroomObject.ALBUM:
            ret['subtext'] = instance.subtext
            ret['total'] = instance.relations_to.count()
        return ret
