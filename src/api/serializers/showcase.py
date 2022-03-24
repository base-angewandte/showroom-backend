import logging

from rest_framework import serializers

from core.models import ShowroomObject

logger = logging.getLogger(__name__)


def get_serialized_showcase_and_warnings(showcase):
    serialized = []
    warnings = []
    for id, showcase_type in showcase:
        try:
            item = ShowroomObject.objects.get(pk=id)
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
            ret['type'] = instance.type
            media = instance.media_set.all()
            # Similar to search results we take the previews from the first image
            # we find in the activity. If there is no image, we'll use thumbnails of
            # a document or the cover of a video, if there are any.
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
                    else:
                        alternative_preview = m.specifics.get('thumbnail')
            if not ret['previews'] and alternative_preview:
                widths = ['640w', '768w', '1024w', '1366w', '1600w', '1632w']
                ret['previews'] = [{w: alternative_preview} for w in widths]
        elif instance.type == ShowroomObject.ALBUM:
            ret['subtext'] = instance.subtitle
            ret['total'] = instance.activities.count()
        return ret
