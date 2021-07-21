from drf_spectacular.utils import OpenApiExample, extend_schema_serializer
from rest_framework import serializers


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            name='With associated entity_id',
            value={
                'id': '0123456789ABCDEF0123456789ABCDEF',
                'name': 'Firstname Lastname',
                'email': 'addy@example.org',
                'entry_id': 'xZy2345aceg98QPT0246aC',
                'groups': ['foo_users', 'bar_members'],
                'permissions': ['view_foo', 'view_bar', 'edit_bar'],
            },
        ),
        OpenApiExample(
            name='Without associated entity_id',
            value={
                'id': '0123456789ABCDEF0123456789ABCDEF',
                'name': 'Firstname Lastname',
                'email': 'addy@example.org',
                'entry_id': None,
                'groups': ['foo_users', 'bar_members'],
                'permissions': ['view_foo', 'view_bar', 'edit_bar'],
            },
        ),
    ],
)
class UserDataSerializer(serializers.Serializer):
    id = serializers.CharField(
        help_text='The user id in the auth backend (i.e. source repo)'
    )
    name = serializers.CharField(help_text='The display name of the user')
    email = serializers.CharField(help_text='The user\'s e-mail address')
    entry_id = serializers.CharField(
        help_text='The user\'s associated showroom entity id. Or null, if no '
        + 'associated showroom entity can be found'
    )
    groups = serializers.ListSerializer(
        child=serializers.CharField(), help_text='The groups this user belongs to.'
    )
    permissions = serializers.ListSerializer(
        child=serializers.CharField(), help_text='The permissions this user has.'
    )