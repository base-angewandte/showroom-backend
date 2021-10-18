import json
import sys
from traceback import print_tb

from rest_framework import serializers

from django.conf import settings

from api.repositories import portfolio
from api.repositories.portfolio import (
    FieldTransformerMissingError,
    MappingNotFoundError,
    transform,
)
from core.models import Activity, Entity

from . import abstract_showroom_object_fields, logger
from .media import MediaSerializer


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
            'keywords',
            'source_repo_data_text',
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
        new_data['keywords'] = (
            {
                kw['label'][settings.LANGUAGE_CODE]: True
                for kw in repo_data.get('keywords')
            }
            if repo_data.get('keywords')
            else {}
        )
        new_data['source_repo_data_text'] = json.dumps(repo_data)

        try:
            new_data['belongs_to'] = Entity.objects.get(
                source_repo_entry_id=data.get('source_repo_owner_id')
            ).id
        except Entity.DoesNotExist:
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
        ret.pop('source_repo_data_text')
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
        # featured_media currently cannot be set explicitly in portfolio
        # therefore we just go through all available media and take the first
        # image we can find
        ret['featured_media'] = None
        for medium in media:
            if medium.type == 'i':
                ret['featured_media'] = MediaSerializer(medium, context=context).data
                break
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

    @staticmethod
    def serialize_related_activity(activity):
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
