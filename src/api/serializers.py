from rest_framework import serializers

from core.models import Activity, Album, Entity, Media

from .repositories import portfolio
from .repositories.portfolio import (
    FieldTransformerMissingError,
    MappingNotFoundError,
    transform,
)

abstract_showroom_object_fields = [
    'id',
    'title',
    'list',
    'primary_details',
    'secondary_details',
    'locations',
    'dates',
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
            'source_repo_data',
            'featured_media',
            'belongs_to',
            'parents',
        ]

    def to_internal_value(self, data):
        new_data = {
            'source_repo_entry_id': data.get('source_repo_entry_id'),
            'source_repo': data.get('source_repo'),
            'belongs_to': data.get('belongs_to'),
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
        new_data.update(transformed)
        return super().to_internal_value(new_data)


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
