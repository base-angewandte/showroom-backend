from rest_framework import serializers

from django.conf import settings

from core.models import Media, ShowroomObject


class MediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        fields = [
            'id',
            'type',
            'file',
            'showroom_object',
            'mime_type',
            'exif',
            'license',
            'specifics',
            'source_repo_media_id',
        ]

    def to_internal_value(self, data):
        # if a new media is posted, we need to inject the repos base url
        # into all properties that represent links
        if self.context['request'].method == 'POST':
            # for link transformations at least file and specifics have to be set
            if 'file' not in data:
                raise serializers.ValidationError({'file': ['This field is required.']})
            if 'specifics' not in data:
                raise serializers.ValidationError(
                    {'specifics': ['This field is required.']}
                )
            # activity also has to be set to an existing activity, so we can get
            # the repos base url
            try:
                activity = ShowroomObject.objects.get(
                    source_repo_object_id=data.get('source_repo_entry_id')
                )
            except ShowroomObject.DoesNotExist:
                raise serializers.ValidationError(
                    {
                        'source_repo_entry_id': [
                            'This field is required and has to refer to an existing'
                            + ' activity by its original source repo\'s entry id.'
                        ]
                    }
                )
            repo_base = activity.source_repo.url_repository
            # now check for links and add the repo_base url
            data['file'] = repo_base + data['file']
            if previews := data['specifics'].get('previews'):
                for preview in previews:
                    for key in preview.keys():
                        preview[key] = repo_base + preview[key]
            if 'thumbnail' in data['specifics']:
                data['specifics']['thumbnail'] = (
                    repo_base + data['specifics']['thumbnail']
                )
            if 'mp3' in data['specifics']:
                data['specifics']['mp3'] = repo_base + data['specifics']['mp3']
            if cover := data['specifics'].get('cover'):
                for key in cover.keys():
                    if type(cover[key]) == str:
                        cover[key] = repo_base + cover[key]
            if playlist := data['specifics'].get('playlist'):
                data['specifics']['playlist'] = repo_base + playlist
        return super().to_internal_value(data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # throw out things we don't need / don't want to show
        ret.pop('showroom_object')  # media are only read-accessible via an activity
        ret.pop('source_repo_media_id')
        ret.pop('exif')
        # rename file to original and add repo_base
        ret['original'] = ret.pop('file')
        # flatten the specifics into the media dict
        specifics = ret.pop('specifics')
        ret.update(specifics)
        # provide a localised license label
        lang = self.context['request'].LANGUAGE_CODE
        if type(instance.license['label']) == dict:
            label = instance.license['label'].get(lang)
            if label:
                ret['license']['label'] = label
            else:
                # if the license label is not available in the requested language
                # we want to provide in the configured default language
                label = instance.license['label'].get(settings.LANGUAGES[0][0])
                if label:
                    ret['license']['label'] = label
                else:
                    # if it is not even available in the default language, we just
                    # take the first label we find
                    keys = list(instance.license['label'])
                    label = instance.license['label'].get(keys[0])
                    ret['license']['label'] = label
        return ret
