from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.db.models import Min

from core.models import ShowroomObject

prefix = settings.FORCE_SCRIPT_NAME


class ActivitiesSitemap(Sitemap):
    def __init__(self, lang='en'):
        super().__init__()
        self.lang = lang

    def items(self):
        """Returns a limited queryset of activities, ordered by currentness."""
        q = ShowroomObject.objects.filter(type=ShowroomObject.ACTIVITY)
        q = q.annotate(rank=Min('daterelevanceindex__rank')).order_by(
            'rank', 'title', 'id'
        )
        return q[: settings.SITEMAP_ACTIVITIES_LIMIT]

    def location(self, item):
        return f'{prefix}/{self.lang}/{item.showroom_id}'


class PeopleSitemap(Sitemap):
    def __init__(self, lang='en'):
        super().__init__()
        self.lang = lang

    def items(self):
        """Returns a queryset of all persons, ordered by name."""
        return ShowroomObject.objects.filter(
            type=ShowroomObject.PERSON,
            active=True,
        ).order_by('title')

    def location(self, item):
        return f'{prefix}/{self.lang}/{item.showroom_id}'
