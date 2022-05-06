from rest_framework import serializers

from core.models import ShowroomObject
from general.utils import slugify

from ..repositories.portfolio import activity_lists
from . import showroom_object_fields
from .generic import CommonTextSerializer, localise_detail_fields
from .showcase import get_serialized_showcase_and_warnings


class EntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ShowroomObject
        fields = showroom_object_fields

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # remove plain repo data
        ret.pop('source_repo')
        ret.pop('source_repo_data')
        ret.pop('source_repo_object_id')
        ret.pop('source_repo_owner_id')
        ret.pop('relations_to')
        ret.pop('belongs_to')

        # transform the id and parent id to include name
        if not instance.title:
            ret['id'] = f'entity-{instance.id}'
        else:
            ret['id'] = f'{slugify(instance.title)}-{instance.id}'
        if instance.belongs_to:
            if not instance.belongs_to.title:
                ret['parent'] = f'entity-{instance.belongs_to.id}'
            else:
                ret[
                    'parent'
                ] = f'{slugify(instance.belongs_to.title)}-{instance.belongs_to.id}'

        # TODO: refactor this (also in get_serach_item(), to be configurable)
        if instance.type == ShowroomObject.PERSON:
            ret['type'] = 'person'
        elif instance.type == ShowroomObject.INSTITUTION:
            ret['type'] = 'institution'
        elif instance.type == ShowroomObject.DEPARTMENT:
            ret['type'] = 'department'

        # make sure to only provide an empty list if showcase is None or {}
        if not instance.entitydetail.showcase:
            instance.entitydetail.showcase = []
        sc, sc_warnings = get_serialized_showcase_and_warnings(
            instance.entitydetail.showcase
        )
        ret['showcase'] = sc
        if sc_warnings:
            ret['showcase_warnings'] = sc_warnings

        # we have to bring list into a format similar to that in activities based
        # on list_ordering
        activity_list = instance.entitydetail.list
        ret['list'] = []
        for order in instance.entitydetail.list_ordering:
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

        # return the localised version of the expertise
        ret['expertise'] = []
        expertise = instance.entitydetail.expertise
        if type(expertise) is dict:
            ret['expertise'] = expertise.get(self.context['request'].LANGUAGE_CODE)

        # now filter out the requested languages for the detail fields and lists
        localise_detail_fields(ret, self.context['request'].LANGUAGE_CODE)

        if photo := instance.entitydetail.photo:
            ret['featured_media'] = {
                'id': instance.entitydetail.photo_id,
                'type': 'i',
                'mime_type': 'image/jpeg',
                'license': {
                    'label': 'Copyright',
                    'source': 'http://base.uni-ak.ac.at/portfolio/licenses/copyright',
                },
                'original': photo,
                'previews': [{'625w': photo}],
                'thumbnail': photo,
            }

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
