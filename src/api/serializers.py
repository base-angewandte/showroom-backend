import logging
import sys
from traceback import print_tb

from rest_framework import serializers

from django.conf import settings

from core.models import Activity, Album, Entity, Media

from .repositories import portfolio
from .repositories.portfolio import (
    FieldTransformerMissingError,
    MappingNotFoundError,
    transform,
)

logger = logging.getLogger(__name__)

abstract_showroom_object_fields = [
    'id',
    'title',
    'subtext',
    'list',
    'primary_details',
    'secondary_details',
    'locations',
    'source_repo',
    'source_repo_entry_id',
]


class EntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Entity
        fields = abstract_showroom_object_fields + [
            'type',
            'expertise',
            'showcase',
            'photo',
            'parent',
        ]


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = abstract_showroom_object_fields + [
            'source_repo_owner_id',
            'source_repo_data',
            'featured_media',
            'belongs_to',
            'relations_to',
            'type',
        ]

    def to_internal_value(self, data):
        new_data = {
            'source_repo_entry_id': data.get('source_repo_entry_id'),
            'source_repo_owner_id': data.get('source_repo_owner_id'),
            'source_repo': data.get('source_repo'),
        }
        repo_data = data.get('data')
        if not type(repo_data) is dict:
            raise serializers.ValidationError(
                {'data': ['Invalid type - has to be an object']}
            )
        entry_type = repo_data.get('type')
        if not type(entry_type) is dict and entry_type is not None:
            raise serializers.ValidationError(
                {'data.type': ['Invalid type - has to be an object or null']}
            )
        new_data['title'] = repo_data.get('title')
        subtext = repo_data.get('subtitle')
        new_data['subtext'] = [subtext] if subtext else []
        new_data['type'] = repo_data.get('type')

        try:
            new_data['belongs_to'] = Entity.objects.get(
                source_repo_entry_id=data.get('source_repo_owner_id')
            ).id
        except Entity.DoesNotExist:
            new_data['belongs_to'] = None
        new_data['source_repo_data'] = repo_data

        # now fetch the schema and apply transformations for the optimised display data
        if entry_type:
            schema = portfolio.get_schema(entry_type.get('source'))
        else:
            schema = '__none__'
        try:
            transformed = transform.transform_data(repo_data, schema)
        except MappingNotFoundError as e:
            # TODO: check why we the 500 response code is ignored and turned into a 400
            raise serializers.ValidationError(
                {
                    'server error': f'No mapping is available to transform entry of type: {e}'
                },
                code=500,
            )
        except FieldTransformerMissingError as e:
            # TODO: check why we the 500 response code is ignored and turned into a 400
            raise serializers.ValidationError(
                {
                    'server error': f'No transformation function is available for field: {e}'
                },
                code=500,
            )
        except Exception as e:
            if settings.DEBUG:
                exc = sys.exc_info()
                logger.error(
                    f'Caught unexpected exception when trying to transform repo data: {e} ({exc[0]})'
                )
                print_tb(exc[2])
            else:
                logger.error(
                    f'Caught unexpected exception when trying to transform repo data: {e}'
                )
            # TODO: check why we the 500 response code is ignored and turned into a 400
            raise serializers.ValidationError(
                {'server error': f'An unexpected error happened: {e}'},
                code=500,
            )
        new_data.update(transformed)
        return super().to_internal_value(new_data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # remove plain repo data
        ret.pop('source_repo')
        ret.pop('source_repo_data')
        ret.pop('source_repo_entry_id')
        ret.pop('source_repo_owner_id')
        ret.pop('relations_to')
        # add timestamps
        ret['date_changed'] = instance.date_changed
        ret['date_created'] = instance.date_created
        # add aggregated media and related activities
        media = instance.media_set.all()
        media_entries = []
        if media:
            context = {'repo_base': instance.source_repo.url_repository}
            media_entries = MediaSerializer(media, many=True, context=context).data
        relations = self.serialize_related()
        ret['entries'] = {
            'media': media_entries,
            'linked': relations,
        }
        # publisher currently is only the entity this activity belongs to
        ret.pop('belongs_to')
        ret['publisher'] = []
        if instance.belongs_to:
            ret['publisher'].append(
                {
                    'name': instance.belongs_to.title,
                    'source': instance.belongs_to.id,
                }
            )
        # include the source institutions details
        ret['source_institution'] = {
            'label': instance.source_repo.label_institution,
            'url': instance.source_repo.url_institution,
            'icon': instance.source_repo.icon,
        }

        # now filter out the requested languages for the detail fields and lists
        new_data = {}
        lang = self.context['request'].LANGUAGE_CODE
        detail_fields = ['primary_details', 'secondary_details', 'list']
        for field in detail_fields:
            new_data[field] = []
            for data in ret[field]:
                if data_localised := data.get(lang):
                    new_data[field].append(data_localised)
                else:
                    # If no localised data could be found, we try to find
                    # another one in the order of the languages defined
                    # in the settings
                    for alt_lang in settings.LANGUAGES:
                        if data_localised := data.get(alt_lang[0]):
                            data_localised['language'] = {
                                'iso': alt_lang[0],
                                'label': {
                                    alt_lang[0]: alt_lang[1],
                                },
                            }
                            new_data[field].append(data_localised)
                            break
                    # Theoretically there could be other localised content in
                    # languages that are not configured in the settings. We
                    # will ignore those.
                    # But if we did internally story a 'default' localisation,
                    # because the data is language independent, we'll use this
                    if data_default := data.get('default'):
                        new_data[field].append(data_default)
            ret.pop(field)
        ret.update(new_data)

        return ret

    def serialize_related(self):
        data = {
            'to': [],
            'from': [],
        }
        for relation in self.instance.relations_to.all():
            data['to'].append(self.serialize_related_activity(relation))
        for relation in self.instance.relations_from.all():
            data['from'].append(self.serialize_related_activity(relation))

        return data

    def serialize_related_activity(self, activity):
        # This should conform to the SearchItem schema
        data = {
            'id': activity.id,
            'alternative_text': [],  # TODO: what should go in here?
            'media_url': '',  # TODO: fill with featured media and rename in api spec (currently: mediaUrl)
            'source': '',  # TODO: ? same as id ?
            'source_institution': activity.source_repo.label_institution,
            'score': None,  # No scoring for related activities
            'title': activity.title,
            'type': activity.type,
        }
        return data


class AlbumSerializer(serializers.ModelSerializer):
    class Meta:
        model = Album
        fields = [
            'id',
            'title',
            'subtitle',
            'secondary_details',
            'belongs_to',
            'activities',
        ]


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
            'source_repo_id',
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
                activity = Activity.objects.get(pk=data.get('activity'))
            except Activity.DoesNotExist:
                raise serializers.ValidationError(
                    {
                        'activity': [
                            'This field is required and has to refer to an existing activity.'
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
        ret.pop('source_repo_id')
        ret.pop('exif')
        # rename file to original and add repo_base
        ret['original'] = ret.pop('file')
        # flatten the specifics into the media dict
        specifics = ret.pop('specifics')
        ret.update(specifics)
        return ret
