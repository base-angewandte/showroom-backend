"""Showroom URL Configuration.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import django_cas_ng.views

from django.conf import settings
from django.contrib import admin
from django.contrib.sitemaps.views import index, sitemap
from django.urls import include, path

from core.sitemap import ActivitiesSitemap, PeopleSitemap

sitemaps = {
    'activities-en': ActivitiesSitemap,
    'activities-de': ActivitiesSitemap(lang='de'),
    'people-en': PeopleSitemap,
    'people-de': PeopleSitemap(lang='de'),
}

urlpatterns = [
    # admin
    path('da/', admin.site.urls),
    # django cas ng
    path(
        'accounts/login/', django_cas_ng.views.LoginView.as_view(), name='cas_ng_login'
    ),
    path(
        'accounts/logout/',
        django_cas_ng.views.LogoutView.as_view(),
        name='cas_ng_logout',
    ),
    path(
        'accounts/callback/',
        django_cas_ng.views.CallbackView.as_view(),
        name='cas_ng_proxy_callback',
    ),
    path('api/', include('api.urls')),
    path(
        'sitemap.xml',
        index,
        {'sitemaps': sitemaps},
        name='django.contrib.sitemaps.views.index',
    ),
    path(
        'sitemap-<section>.xml',
        sitemap,
        {'sitemaps': sitemaps},
        name='django.contrib.sitemaps.views.sitemap',
    ),
    path(settings.DOCS_URL, include('docs.urls')),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
