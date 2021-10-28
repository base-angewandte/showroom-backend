from rest_framework import serializers

from api.serializers.search import (
    SearchFilterSerializer,
    SearchItemSerializer,
    SearchItemSourceInstitutionSerializer,
)


class InitialSearchResultSerializer(serializers.Serializer):
    label = serializers.CharField()
    total = serializers.IntegerField()
    data = SearchItemSerializer(many=True)
    filters = SearchFilterSerializer(many=True)


class InitialDataSerializer(serializers.Serializer):
    id = serializers.CharField(
        help_text='Entity ID of the institution managing the start page'
    )
    source_institution = SearchItemSourceInstitutionSerializer()
    showcase = serializers.ListSerializer(
        child=serializers.JSONField(),
        help_text='The showcase object of the entity referred by ID, which is displayed as the start page carousel',
    )
    results = InitialSearchResultSerializer(
        many=True,
        help_text='The data needed for initial display of recent events, starred items, etc. and information about the filter used in that category',
    )
