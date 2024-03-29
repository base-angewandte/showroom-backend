from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularJSONAPIView,
    SpectacularSwaggerView,
)
from rest_framework.routers import DefaultRouter

from django.urls import include, path

from . import plugins
from .views.activity import ActivityViewSet
from .views.album import AlbumViewSet
from .views.autocomplete import AutocompleteViewSet
from .views.entity import EntityViewSet
from .views.filter import FilterViewSet
from .views.initial import InitialViewSet
from .views.media import MediaViewSet
from .views.search import SearchViewSet
from .views.showcase_search import ShowcaseSearchViewSet
from .views.user import get_user_data

router = DefaultRouter()
router.register(r'entities', EntityViewSet)
router.register(r'activities', ActivityViewSet)
router.register(r'albums', AlbumViewSet)
router.register(r'media', MediaViewSet)
router.register(r'search', SearchViewSet, basename='search')
router.register(r'filters', FilterViewSet, basename='filters')
router.register(r'autocomplete', AutocompleteViewSet, basename='autocomplete')
router.register(r'initial', InitialViewSet, basename='initial')
router.register(r'showcase_search', ShowcaseSearchViewSet, basename='showcase_search')

urlpatterns = [
    path('', include(router.urls)),
    path('user/', get_user_data, name='user'),
    path('openapi.yaml', SpectacularAPIView.as_view(), name='schema_yaml'),
    path('openapi.json', SpectacularJSONAPIView.as_view(), name='schema_json'),
    path(
        'docs/',
        SpectacularSwaggerView.as_view(url_name='schema_json'),
        name='swagger-ui',
    ),
]

urlpatterns.extend(plugins.get_url_patterns())
