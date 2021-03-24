# from django.shortcuts import render
from rest_framework import viewsets

from core.models import Activity, Album, Entity, Media, SourceRepository

from .serializers import SourceRepositorySerializer

# Create your views here.


class SourceRepositoryViewSet(viewsets.ModelViewSet):
    queryset = SourceRepository.objects.all()
    serializer_class = SourceRepositorySerializer


class EntityViewSet(viewsets.ModelViewSet):
    queryset = Entity.objects.all()


class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.all()


class AlbumViewSet(viewsets.ModelViewSet):
    queryset = Album.objects.all()


class MediaViewSet(viewsets.ModelViewSet):
    queryset = Media.objects.all()
