from drf_spectacular.utils import (
    OpenApiExample,
    extend_schema_field,
    extend_schema_serializer,
)
from rest_framework import serializers


@extend_schema_field(
    field={'type': 'string', 'enum': ['text', 'date', 'daterange', 'chips']},
    component_name='FilterTypes',
)
class FilterTypesField(serializers.ChoiceField):
    def __init__(self, **kwargs):
        if 'choices' in kwargs:
            kwargs.pop('choices')

        super().__init__(choices=['text', 'date', 'daterange', 'chips'], **kwargs)


class ChipsFilterOptionsSerializer(serializers.Serializer):
    id = serializers.CharField(help_text='The non-localised default value')
    label = serializers.CharField(help_text='The localised label of this value')


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            name='Activities, persons, date range and keywords filter',
            value=[
                {
                    'id': 'activities',
                    'label': 'Activities',
                    'type': 'text',
                },
                {
                    'id': 'persons',
                    'label': 'Persons',
                    'type': 'text',
                },
                {
                    'id': 'date_range',
                    'label': 'Date Range',
                    'type': 'daterange',
                },
                {
                    'id': 'keywords',
                    'type': 'chios',
                    'label': 'Keywords',
                    'freetext_allowed': False,
                    'options': [
                        {'id': 'Assemblage', 'label': 'Assemblage'},
                        {'id': 'Community Radio', 'label': 'Community Radio'},
                        {'id': 'Explosion Research', 'label': 'Explosion Research'},
                    ],
                },
            ],
        ),
    ],
)
class FilterSerializer(serializers.Serializer):
    id = serializers.CharField(
        help_text='The label to identify this filter in search queries'
    )
    type = FilterTypesField()
    label = serializers.CharField(help_text='Localised label for this filter')
    # The following fields are only used for 'chips' filters
    options = ChipsFilterOptionsSerializer(
        many=True,
        required=False,
        help_text='All selectable options in case of a chips type filter',
    )
    freetext_allowed = serializers.BooleanField(
        required=False,
        help_text='In case of a chips type filter, whether only the provided options'
        + ' can be searched for or freetext is allowed additionally',
    )
