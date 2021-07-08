from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularJSONAPIView,
    SpectacularSwaggerView,
)
from rest_framework.routers import DefaultRouter

from django.urls import include, path

from . import views

router = DefaultRouter()
router.register(r'entities', views.EntityViewSet)
router.register(r'activities', views.ActivityViewSet)
router.register(r'albums', views.AlbumViewSet)
router.register(r'media', views.MediaViewSet)
router.register(r'search', views.SearchViewSet, basename='search')
router.register(r'filters', views.FilterViewSet, basename='filters')
router.register(r'autocomplete', views.AutocompleteViewSet, basename='autocomplete')
router.register(r'relations', views.RelationViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('schema/openapi3.yaml', SpectacularAPIView.as_view(), name='schema'),
    path('schema/openapi3.json', SpectacularJSONAPIView.as_view(), name='schema'),
    path(
        'schema/swagger-ui',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui',
    ),
]
