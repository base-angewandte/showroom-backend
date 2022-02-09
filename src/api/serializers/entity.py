from rest_framework import serializers

from django.utils.text import slugify

from core.models import Entity

from ..repositories.portfolio import activity_lists
from . import abstract_showroom_object_fields
from .generic import CommonTextSerializer, localise_detail_fields
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

        # we have to bring list into a format similar to that in activities based
        # on list_ordering
        activity_list = ret.pop('list')
        ret['list'] = []
        for order in instance.list_ordering:
            if order['hidden']:
                continue
            if (list_id := order['id']) in activity_list:
                # we don't want to add empty lists, but we will add them, if at least
                # one item is available in any translation (even if another
                # translation is empty)
                add_list = False
                for lang in activity_list[list_id]:
                    if activity_list[list_id][lang]['data']:
                        add_list = True
                if add_list:
                    ret['list'].append(activity_list[list_id])

        # now filter out the requested languages for the detail fields and lists
        localise_detail_fields(ret, self.context['request'].LANGUAGE_CODE)

        return ret


class EntityShowcaseEditSerializer(serializers.Serializer):
    id = serializers.CharField()
    type = serializers.ChoiceField(
        choices=['activity', 'album', 'entity'],
        help_text='The type of showcase object. Defaults to activity, if not specified',
        required=False,
    )


class EntitySecondaryDetailsEditSerializer(serializers.Serializer):
    en = CommonTextSerializer(required=False)
    de = CommonTextSerializer(required=False)
    xx = CommonTextSerializer(required=False)

    def to_internal_value(self, data):
        # check that every property in data has a 2 letter key
        # and conforms to the CommonText schema
        for key in data:
            if len(key) != 2:
                raise serializers.ValidationError(
                    'Object keys have to be 2-letter language codes'
                )
            s = CommonTextSerializer(data=data[key])
            s.is_valid(raise_exception=True)
        return data


class EntityEditSerializer(serializers.Serializer):
    secondary_details = EntitySecondaryDetailsEditSerializer(many=True, required=False)
    showcase = EntityShowcaseEditSerializer(many=True, required=False)


class EntityListEditSerializer(serializers.Serializer):
    id = serializers.CharField()
    hidden = serializers.BooleanField(default=False, required=False)

    def to_internal_value(self, data):
        if not (id := data.get('id')):
            raise serializers.ValidationError(
                'id has to be set and must be non-zero-len string'
            )
        if id not in activity_lists.list_collections:
            raise serializers.ValidationError(
                'id is not a valid activity list collection'
            )
        if (hidden := data.get('hidden')) is None:
            data['hidden'] = False
        else:
            if type(hidden) is not bool:
                raise serializers.ValidationError('hidden has to be boolean')
        return data
