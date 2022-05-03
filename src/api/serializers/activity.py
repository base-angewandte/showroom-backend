from rest_framework import serializers

from api.repositories import portfolio
from api.repositories.portfolio import (
    FieldTransformerMissingError,
    MappingNotFoundError,
    transform,
)
from core.models import ShowroomObject
from general.datetime.utils import format_datetime

from ..repositories.portfolio.search import get_search_item
from . import logger, showroom_object_fields
from .generic import localise_detail_fields
from .media import MediaSerializer


class ActivityRelationSerializer(serializers.Serializer):
    activity_id = serializers.CharField()


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ShowroomObject
        fields = showroom_object_fields

    def get_unique_together_validators(self):
        # disable unique together checks
        return []

    def to_internal_value(self, data):
        new_data = {
            'source_repo_object_id': data.get('source_repo_entry_id'),
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
        new_data['type'] = ShowroomObject.ACTIVITY

        try:
            new_data['belongs_to'] = ShowroomObject.active_objects.get(
                source_repo_object_id=data.get('source_repo_owner_id')
            ).id
        except ShowroomObject.DoesNotExist:
            new_data['belongs_to'] = None
        new_data['source_repo_data'] = repo_data

        # now fetch the schema and apply transformations for optimised display data
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
            ) from e
        except FieldTransformerMissingError as e:
            # TODO: check why we the 500 response code is ignored and turned into a 400
            raise serializers.ValidationError(
                {
                    'server error': f'No transformation function is available for field: {e}'
                },
                code=500,
            ) from e
        except Exception as e:
            logger.exception(
                'Caught unexpected exception when trying to transform repo data'
            )
            # TODO: check why we the 500 response code is ignored and turned into a 400
            raise serializers.ValidationError(
                {'server error': f'An unexpected error happened: {e}'},
                code=500,
            ) from e
        new_data.update(transformed)
        return super().to_internal_value(new_data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # remove plain repo data
        ret.pop('source_repo')
        ret.pop('source_repo_data')
        ret.pop('source_repo_object_id')
        ret.pop('source_repo_owner_id')
        ret.pop('relations_to')
        # set type to activity type (instead of showroom object type) and add keywords
        ret['type'] = instance.activitydetail.activity_type
        ret['keywords'] = instance.activitydetail.keywords
        # add timestamps
        ret['date_changed'] = instance.date_changed
        ret['date_created'] = instance.date_created
        # add aggregated media and related activities
        media = instance.media_set.all()
        media_entries = []
        if media:
            context = {
                'repo_base': instance.source_repo.url_repository,
                'request': self.context.get('request'),
            }
            media_entries = MediaSerializer(media, many=True, context=context).data
        relations = self.serialize_related()
        ret['entries'] = {
            'media': media_entries,
            'linked': relations,
        }
        # in case a featured medium is set, we'll use this. if non is set explicitly
        # we search if there is any image attached to the entry and take this one.
        ret['featured_media'] = None
        featured_medium = media.filter(featured=True)
        if featured_medium:
            ret['featured_media'] = MediaSerializer(
                featured_medium[0], context=context
            ).data
        else:
            for medium in media:
                if medium.type == 'i':
                    ret['featured_media'] = MediaSerializer(
                        medium, context=context
                    ).data
                    break
        # publisher currently is only the entity this activity belongs to
        ret.pop('belongs_to')
        # TODO remove publisher and source_institution as soon as FE has been adapted
        #      to use publishing_info
        ret['publisher'] = []
        if instance.belongs_to:
            publisher = {'name': instance.belongs_to.title}
            if instance.belongs_to.active:
                publisher['source'] = instance.belongs_to.showroom_id
            ret['publisher'].append(publisher)
        ret['source_institution'] = {
            'label': instance.source_repo.label_institution,
            'url': instance.source_repo.url_institution,
            'icon': instance.source_repo.icon,
        }
        ret['publishing_info'] = {
            'publisher': ret['publisher'],
            'date_published': format_datetime(instance.date_created),
            'date_updated': format_datetime(instance.date_synced),
            'source_institution': ret['source_institution'],
        }

        # now filter out the requested languages for the detail fields and lists
        localise_detail_fields(ret, self.context['request'].LANGUAGE_CODE)

        return ret

    def serialize_related(self):
        lang = self.context['request'].LANGUAGE_CODE
        data = {
            'to': [],
            'from': [],
        }
        # filter out entities
        for relation in self.instance.relations_to.filter(type=self.instance.ACTIVITY):
            data['to'].append(get_search_item(relation, lang))
        for relation in self.instance.relations_from.filter(
            type=self.instance.ACTIVITY
        ):
            data['from'].append(get_search_item(relation, lang))

        return data
