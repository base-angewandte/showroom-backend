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
            'parents',
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
        if not entry_type:
            raise serializers.ValidationError(
                {'data.type': ['This field may not be null.']}
            )
        if not type(entry_type) is dict:
            raise serializers.ValidationError(
                {'data.type': ['Invalid type - has to be an object']}
            )
        new_data['title'] = repo_data.get('title')
        new_data['subtext'] = [repo_data.get('subtitle')]
        new_data['type'] = repo_data.get('type')

        try:
            new_data['belongs_to'] = Entity.objects.get(
                source_repo_entry_id=data.get('source_repo_owner_id')
            ).id
        except Entity.DoesNotExist:
            new_data['belongs_to'] = None
        new_data['source_repo_data'] = repo_data

        # now fetch the schema and apply transformations for the optimised display data
        schema = portfolio.get_schema(entry_type.get('source'))
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
        # add timestamps
        ret['date_changed'] = instance.date_changed
        ret['date_created'] = instance.date_created
        # TODO: entries are currently empty, until media and relations are pushed
        ret['entries'] = {
            'media': [],
            'linked': [],
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
        fields = ['id', 'type', 'file', 'activity', 'mime_type', 'exif', 'license']
