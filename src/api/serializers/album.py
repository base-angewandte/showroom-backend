from rest_framework import serializers

from core.models import Album


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
