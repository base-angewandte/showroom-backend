from rest_framework_api_key.models import AbstractAPIKey

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_ipv46_address
from django.db import models

available_plugins = ', '.join(settings.API_PLUGINS)


def get_default_allowed_ips():
    return ['*']


def validate_plugins(value):
    if type(value) is not list:
        raise ValidationError('has to be a list')
    for item in value:
        if type(item) is not str:
            raise ValidationError('only strings are allowed in the plugin list')
        if item not in settings.API_PLUGINS:
            raise ValidationError(f'{item} is not available as a plugin')
    return True


def validate_ips(value):
    if type(value) is not list:
        raise ValidationError('has to be a list of strings')
    for item in value:
        if type(item) is not str:
            raise ValidationError('list items have to be strings')
        if item == '*':
            continue
        try:
            validate_ipv46_address(item)
        except ValidationError as err:
            raise ValidationError(f'{item} is not a valid IP address') from err
    return True


class PluginAPIKey(AbstractAPIKey):
    active = models.BooleanField(default=True)
    plugins = models.JSONField(
        default=list,
        help_text='JSON list of plugins that can be used with this key. See API plugins section in the docs for available plugins.',
        validators=[validate_plugins],
        blank=True,
    )
    allowed_ips = models.JSONField(
        default=get_default_allowed_ips,
        help_text='JSON list of IPs that are allowed to use this key. Use * for any.',
        validators=[validate_ips],
    )
    note = models.TextField(blank=True, help_text='Optional internal note for admins.')

    class Meta:
        verbose_name = 'Plugin API key'
        verbose_name_plural = 'Plugin API keys'
