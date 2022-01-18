from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema_field,
    inline_serializer,
)
from rest_framework import serializers

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
class CommonTextDataItemSerializer(serializers.JSONField):
    # TODO: add a custom validation function
    pass


class CommonTextSerializer(serializers.Serializer):
    label = serializers.CharField()
    data = serializers.ListSerializer(child=CommonTextDataItemSerializer())
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
