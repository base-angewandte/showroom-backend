from rest_framework import serializers

from django.utils.text import slugify

from core.models import Entity

from . import abstract_showroom_object_fields
from .showcase import get_serialized_showcase_and_warnings


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

    def to_representation(self, instance):
        ret = super().to_representation(instance)

        # transform the id and parent id to include name
        if not instance.title:
            ret['id'] = f'entity-{instance.id}'
        else:
            ret['id'] = f'{slugify(instance.title)}-{instance.id}'
        if instance.parent:
            if not instance.parent.title:
                ret['parent'] = f'entity-{instance.parent.id}'
            else:
                ret['parent'] = f'{slugify(instance.parent.title)}-{instance.parent.id}'

        # TODO: refactor this (also in get_serach_item(), to be configurable)
        if instance.type == 'P':
            ret['type'] = 'person'
        elif instance.type == 'I':
            ret['type'] = 'institution'
        elif instance.type == 'D':
            ret['type'] = 'department'

        # make sure to only provide an empty list if showcase is None or {}
        if not instance.showcase:
            instance.showcase = []
        sc, sc_warnings = get_serialized_showcase_and_warnings(instance.showcase)
        ret['showcase'] = sc
        if sc_warnings:
            ret['showcase_warnings'] = sc_warnings

        return ret


class EntityEditItemSerializer(serializers.Serializer):
    id = serializers.CharField()
