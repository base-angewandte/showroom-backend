from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularJSONAPIView,
    SpectacularSwaggerView,
)
from rest_framework.routers import DefaultRouter

from django.urls import include, path

from .views.activity import ActivityViewSet
from .views.album import AlbumViewSet
from .views.autocomplete import AutocompleteViewSet
from .views.category import CategoryViewSet
from .views.entity import EntityViewSet
from .views.filter import FilterViewSet
from .views.media import MediaViewSet
from .views.search import SearchViewSet
from .views.user import get_user_data

router = DefaultRouter()
router.register(r'entities', EntityViewSet)
router.register(r'activities', ActivityViewSet)
router.register(r'albums', AlbumViewSet)
router.register(r'media', MediaViewSet)
router.register(r'search', SearchViewSet, basename='search')
router.register(r'filters', FilterViewSet, basename='filters')
router.register(r'autocomplete', AutocompleteViewSet, basename='autocomplete')
router.register(r'categories', CategoryViewSet, basename='categories')

urlpatterns = [
    path('', include(router.urls)),
    path('user/', get_user_data, name='user'),
    path('schema/openapi3.yaml', SpectacularAPIView.as_view(), name='schema'),
    path('schema/openapi3.json', SpectacularJSONAPIView.as_view(), name='schema'),
    path(
        'schema/swagger-ui',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui',
    ),
]
