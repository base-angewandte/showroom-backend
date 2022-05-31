from rest_framework_api_key.admin import APIKeyModelAdmin
from rest_framework_api_key.models import APIKey

from django.contrib import admin

from .models import PluginAPIKey


class PluginAPIKeyAdmin(APIKeyModelAdmin):
    pass


admin.site.register(PluginAPIKey, PluginAPIKeyAdmin)
# As it would be confusing to have generic API keys next to our specific ones, we'll
# unregister them from the admin interface
admin.site.unregister(APIKey)
