from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema_field,
    inline_serializer,
)
from rest_framework import serializers

from django.conf import settings

error_schema = inline_serializer(
    name='Error',
    fields={
        'detail': serializers.CharField(help_text='A message describing the error'),
    },
)


def error(
    description: str = 'A generic error response',
    detail: str = 'A message describing the error',
    status_code: int = None,
):
    status_codes = (
        [str(status_code)]
        if status_code
        else ['400', '401', '403', '404', '405', '500']
    )
    return OpenApiResponse(
        description=description,
        response=error_schema,
        examples=[
            OpenApiExample(
                name='Error',
                value={'detail': detail},
                # all response codes that will potentially use this example have to be listed here:
                status_codes=status_codes,
            ),
        ],
    )


def localise_detail_fields(data, lang):
    """Goes through Entity/Activity data and replaces detail fields with their
    localised version."""

    new_data = {}
    detail_fields = ['primary_details', 'secondary_details', 'list']
    for field in detail_fields:
        new_data[field] = []
        for data_item in data[field]:
            if data_localised := data_item.get(lang):
                new_data[field].append(data_localised)
            else:
                # If no localised data could be found, we try to find
                # another one in the order of the languages defined
                # in the settings
                for alt_lang in settings.LANGUAGES:
                    if data_localised := data_item.get(alt_lang[0]):
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
                if data_default := data_item.get('default'):
                    new_data[field].append(data_default)
        data.pop(field)
    data.update(new_data)


@extend_schema_field(
    field={
        'oneOf': [
            {
                'type': 'object',
                'description': 'a recursive CommonList entry',
            },
            {
                'type': 'object',
                'description': 'a CommonListItem without any further recursion',
                'properties': {
                    'attributes': {
                        'type': 'array',
                        'items': {'type': 'string'},
                    },
                    'value': {'type': 'string'},
                    'id': {'type': 'string'},
                },
            },
        ]
    }
)
class CommonListDataField(serializers.JSONField):
    pass


class CommonListSerializer(serializers.Serializer):
    id = serializers.CharField()
    labels = serializers.CharField()
    hidden = serializers.BooleanField(required=False)
    data = serializers.ListField(child=CommonListDataField())


class LanguageLabelSerializer(serializers.Serializer):
    en = serializers.CharField()
    de = serializers.CharField()
    xx = serializers.CharField()


class LanguageSerializer(serializers.Serializer):
    iso = serializers.CharField(
        help_text='The ISO 2 letter code for the language this content was returned in'
    )
    label = LanguageLabelSerializer(
        help_text='Contains all available translations of the label that should be used if the language of the content is to be rendered.'
    )


@extend_schema_field(
    field={
        'oneOf': [
            {'type': 'string', 'example': 'A generic standalone label'},
            {
                'type': 'array',
                'items': {'type': 'string'},
                'example': ['Item 1', 'Item 2', 'Item 3'],
            },
            {
                'type': 'object',
                'properties': {
                    'label': {
                        'type': 'string',
                        'example': 'www',
                        'description': 'A label prefix',
                    },
                    'value': {
                        'type': 'string',
                        'example': 'example.org',
                        'description': 'The actual label content',
                    },
                    'url': {
                        'type': 'string',
                        'example': 'https://example.org',
                        'description': 'An optional link for this item',
                    },
                    'source': {
                        'type': 'string',
                        'example': 'jane-doe-d2JnH6L5WAdj7sQzZTRhUC',
                        'description': 'An optional internal object (e.g. entity) id',
                    },
                    'additional': {
                        'type': 'array',
                        'description': 'Optional list of labels for a tooltip',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'label': {
                                    'type': 'string',
                                    'example': 'Weblink',
                                },
                                'value': {
                                    'type': 'string',
                                    'example': 'example.org',
                                },
                                'url': {
                                    'type': 'string',
                                    'example': 'https://example.com',
                                },
                            },
                        },
                    },
                },
                'required': ['label', 'value'],
            },
        ],
    },
)
class CommonTextDataSerializer(serializers.JSONField):
    def to_internal_value(self, data):
        # validate the data to conform to the CommonText.data schema
        if not type(data) in [str, list]:
            raise serializers.ValidationError(
                f'Incorrect type for data. Expected str or list, but got {type(data).__name__}'
            )
        if type(data) is list:
            for item in data:
                if not type(item) in [str, dict]:
                    raise serializers.ValidationError(
                        f'Incorrect type for data. Expected list[str] or list[dict], but got list[{type(item).__name__}]'
                    )
                if type(item) is dict:
                    if 'label' not in item:
                        raise serializers.ValidationError(
                            'label is a required property of CommonTextObject'
                        )
                    if 'value' not in item:
                        raise serializers.ValidationError(
                            'value is a required property of CommonTextObject'
                        )
                    if type(item['label']) is not str:
                        raise serializers.ValidationError(
                            f'Incorrect type for CommonTextObject label. Expected str, but got {type(item["label"]).__name__}'
                        )
                    if type(item['value']) is not str:
                        raise serializers.ValidationError(
                            f'Incorrect type for CommonTextObject value. Expected str, but got {type(item["value"]).__name__}'
                        )
                    if 'url' in item and type(item['url']) is not str:
                        raise serializers.ValidationError(
                            f'Incorrect type for CommonTextObject url. Expected str, but got {type(item["url"]).__name__}'
                        )
                    if 'source' in item and type(item['source']) is not str:
                        raise serializers.ValidationError(
                            f'Incorrect type for CommonTextObject source. Expected str, but got {type(item["source"]).__name__}'
                        )
                    if 'additional' in item:
                        if type(item['additional']) is not list:
                            raise serializers.ValidationError(
                                f'Incorrect type for CommonTextObject additional. Expected list, but got {type(item["additional"]).__name__}'
                            )
                        for additional_item in item['additional']:
                            if type(additional_item) is not dict:
                                raise serializers.ValidationError(
                                    f'Incorrect type for CommonTextObject additional item. Expected dict, but got {type(additional_item).__name__}'
                                )
                            if (
                                'label' in additional_item
                                and type(additional_item['label']) is not str
                            ):
                                raise serializers.ValidationError(
                                    f'Incorrect type for CommonTextObject additional item label. Expected str, but got {type(additional_item["label"]).__name__}'
                                )
                            if (
                                'value' in additional_item
                                and type(additional_item['value']) is not str
                            ):
                                raise serializers.ValidationError(
                                    f'Incorrect type for CommonTextObject additional item value. Expected str, but got {type(additional_item["value"]).__name__}'
                                )
                            if (
                                'url' in additional_item
                                and type(additional_item['url']) is not str
                            ):
                                raise serializers.ValidationError(
                                    f'Incorrect type for CommonTextObject additional item url. Expected str, but got {type(additional_item["url"]).__name__}'
                                )

        return data


class CommonTextSerializer(serializers.Serializer):
    label = serializers.CharField()
    data = CommonTextDataSerializer()
    language = LanguageSerializer(
        required=False,
        help_text='This property will only be set, if the requested language could not be found',
    )


class Responses:
    Error400 = error(
        status_code=400,
        description='Bad Request',
        detail='Something with your request is wrong. This message should provide more details.',
    )
    Error403 = error(
        status_code=403,
        description='Forbidden',
        detail='Authentication credentials were not provided.',
    )  # this is the DRF default reply for 404
    Error404 = error(
        status_code=404, description='Not Found', detail='Not found.'
    )  # this is the DRF default reply for 404

    CommonList = OpenApiResponse(
        description='a list of things',
        response=CommonListSerializer,
        # TODO: add examples
    )

    RelationAdded = OpenApiResponse(
        description='The relationship was successfully added.',
        response=None,
    )
