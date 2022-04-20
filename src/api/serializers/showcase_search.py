from rest_framework import serializers

from django.conf import settings


class ShowcaseSearchSerializer(serializers.Serializer):
    q = serializers.CharField(
        required=False,
        help_text='Search string to look for in all showroom activities (or those limited by entity_id).',
    )
    entity_id = serializers.CharField(
        required=False,
        help_text='Limit the search to objects belonging to this person or institution.',
    )
    exclude = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text='List of object IDs that should be excluded from the result set.',
    )
    sort = serializers.ChoiceField(
        required=False,
        choices=['title', 'date_changed', '-title', '-date_changed'],
        help_text='Order results alphabetically or by modified date, ascending or (-) descending. Default: title',
    )
    limit = serializers.IntegerField(
        required=False,
        help_text=f'Limit the number of results. Default: {settings.SEARCH_LIMIT}',
    )
    offset = serializers.IntegerField(
        required=False, help_text='Offset for the first item in the results set.'
    )
