from rest_framework import serializers

from core.models import Activity, Media


class MediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        fields = [
            'id',
            'type',
            'file',
            'activity',
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
                activity = Activity.objects.get(
                    source_repo_entry_id=data.get('source_repo_entry_id')
                )
            except Activity.DoesNotExist:
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
                    cover[key] = repo_base + cover[key]
            if 'playlist' in data['specifics']:
                data['specifics']['playlist'] = (
                    repo_base + data['specifics']['playlist']
                )
        return super().to_internal_value(data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # throw out things we don't need / don't want to show
        ret.pop('activity')  # media are only read-accessible via an activity
        ret.pop('source_repo_media_id')
        ret.pop('exif')
        # rename file to original and add repo_base
        ret['original'] = ret.pop('file')
        # flatten the specifics into the media dict
        specifics = ret.pop('specifics')
        ret.update(specifics)
        return ret