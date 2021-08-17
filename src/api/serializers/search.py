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
    category = serializers.CharField(
        required=False,
        help_text='If only a certain category of showroom objects should be returned.'
        + ' Currently this can either be persons or activities',
    )
    limit = serializers.IntegerField(required=False)
    offset = serializers.IntegerField(required=False)


class SearchItemAlternativeTextSerializer(serializers.Serializer):
    label = serializers.CharField()
    value = serializers.CharField()


class SearchItemSourceInstitutionSerializer(serializers.Serializer):
    label = serializers.CharField()
    url = serializers.URLField()
    icon = serializers.URLField()


class SearchItemSerializer(serializers.Serializer):
    id = serializers.CharField()
    alternative_text = SearchItemAlternativeTextSerializer(many=True)
    media_url = serializers.URLField()
    source = serializers.URLField()
    source_institution = SearchItemSourceInstitutionSerializer()
    score = serializers.IntegerField()
    title = serializers.CharField()
    type = serializers.CharField()


# TODO: add some examples to the schema
class SearchResultSerializer(serializers.Serializer):
    collection = serializers.CharField()
    total = serializers.IntegerField()
    data = SearchItemSerializer(many=True)
