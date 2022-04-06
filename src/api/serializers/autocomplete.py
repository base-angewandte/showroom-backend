from rest_framework import serializers


class AutocompleteItemDataSerializer(serializers.Serializer):
    id = serializers.CharField()  # ShortUUID
    title = serializers.CharField()
    subtext = serializers.ListField(child=serializers.CharField())


class AutocompleteItemSerializer(serializers.Serializer):
    source = serializers.CharField()
    label = serializers.CharField()
    data = AutocompleteItemDataSerializer(many=True)


class AutocompleteRequestSerializer(serializers.Serializer):
    q = serializers.CharField()
    filter_id = serializers.CharField(required=False, default='fulltext')
    limit = serializers.IntegerField(required=False)
