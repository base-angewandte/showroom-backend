from rest_framework import serializers

from django.conf import settings


class SearchFilterSerializer(serializers.Serializer):
    id = serializers.CharField(
        help_text='id of the filter as obtained from the /filters endpoint'
    )
    # TODO: either create some polymorphic serializer here for validation or
    #       otherwise annotate the schema accordingly
    #       filter_values can be any of:
    #       - string
    #       - date
    #       - {'from': date, 'to': date}
    #       - {'id': string, 'label': string}
    filter_values = serializers.ListField(
        child=serializers.JSONField(),
        help_text='Array of either strings, dates, date ranges or a chips options.'
        + ' Multiple values will be combined in a logical OR.',
    )


# TODO: add some examples to the schema
class SearchRequestSerializer(serializers.Serializer):
    filters = serializers.ListField(
        child=SearchFilterSerializer(),
        help_text='Array of logical AND filters that should be applied to the search.',
    )
    limit = serializers.IntegerField(
        required=False,
        help_text=f'Limit the number of results. Default: {settings.SEARCH_LIMIT}',
    )
    offset = serializers.IntegerField(
        required=False,
        help_text='Offset for the first item in the results set.',
    )
    order_by = serializers.ChoiceField(
        required=False,
        default='default',
        choices=[
            'currentness',
            'rank',
            'default',
            'title',
            '-title',
            'date_changed',
            '-date_changed',
        ],
    )


class SearchItemSourceInstitutionSerializer(serializers.Serializer):
    label = serializers.CharField(
        help_text='Name of institution',
    )
    url = serializers.URLField(
        help_text='URL to institution or the institution\'s showroom page',
    )
    icon = serializers.URLField(
        help_text='Path to the institution\'s icon file',
    )


class SearchItemSerializer(serializers.Serializer):
    id = serializers.CharField()
    type = serializers.CharField()
    title = serializers.CharField()
    subtitle = serializers.CharField()
    description = serializers.CharField()
    alternative_text = serializers.ListField(child=serializers.CharField())
    image_url = serializers.URLField()
    source_institution = SearchItemSourceInstitutionSerializer()
    score = serializers.IntegerField()


# TODO: add some examples to the schema
class SearchResultSerializer(serializers.Serializer):
    label = serializers.CharField()
    total = serializers.IntegerField()
    data = SearchItemSerializer(many=True)
