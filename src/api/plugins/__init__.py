from django.conf import settings
from django.urls import re_path

from .repo_source import RepoSourceView


def get_url_patterns():
    patterns = []

    if 'repo_source' in settings.API_PLUGINS:
        patterns.append(
            re_path('activities/(?P<pk>[^/.]+)/repo_source/$', RepoSourceView.as_view())
        )

    return patterns
