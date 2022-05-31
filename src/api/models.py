from rest_framework_api_key.models import AbstractAPIKey

from django.db import models


def get_default_allowed_ips():
    return ['*']


class PluginAPIKey(AbstractAPIKey):
    active = models.BooleanField(default=True)
    plugins = models.JSONField(
        default=list,
        help_text='List of plugins that can be used with this key.',
    )
    allowed_ips = models.JSONField(
        default=get_default_allowed_ips,
        help_text='List of IPs that are allowed to use this key. Use * for any.',
    )
    note = models.TextField(help_text='Optional internal note for admins.')

    class Meta:
        verbose_name = 'Plugin API key'
        verbose_name_plural = 'Plugin API keys'
