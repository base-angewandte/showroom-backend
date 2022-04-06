from rest_framework import serializers


class AutocompleteDataSerializer(serializers.Serializer):
    id = serializers.CharField()  # ShortUUID
    title = serializers.CharField()
    subtext = serializers.ListField(child=serializers.CharField())


class AutocompleteSerializer(serializers.Serializer):
    filter_id = serializers.CharField(
        help_text='The filter_id that has to be applied if an id from the search result should be used to refine the search.',
    )
    label = serializers.CharField(
        help_text='The label to display for this type of result objects.'
    )
    data = AutocompleteDataSerializer(
        many=True,
        help_text='A list of autocomplete items within this type of result objects.',
    )


class AutocompleteRequestSerializer(serializers.Serializer):
    q = serializers.CharField()
    filter_id = serializers.CharField(required=False, default='fulltext')
    limit = serializers.IntegerField(required=False)
