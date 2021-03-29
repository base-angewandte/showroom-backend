from rest_framework import serializers

from core.models import Activity, Album, Entity, Media

abstract_showroom_object_fields = [
    'id',
    'title',
    'list',
    'primary_details',
    'secondary_details',
    'locations',
    'dates',
    'source_repo',
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
            'type',
            'featured_media',
            'belongs_to',
            'parents',
        ]


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
