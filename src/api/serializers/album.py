from rest_framework import serializers

from core.models import ShowroomObject


class AlbumSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShowroomObject
        fields = [
            'id',
            'title',
            'subtext',
            'secondary_details',
            'belongs_to',
            'relations_to',
        ]
