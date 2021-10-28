from rest_framework import serializers


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
    limit = serializers.IntegerField(required=False)
    offset = serializers.IntegerField(required=False)


class SearchItemSourceInstitutionSerializer(serializers.Serializer):
    label = serializers.CharField()
    url = serializers.URLField()
    icon = serializers.URLField()


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
