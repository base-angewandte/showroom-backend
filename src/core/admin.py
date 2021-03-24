from django.contrib import admin

from .models import Activity, Album, Entity, Media, SourceRepository

admin.site.register(SourceRepository)
admin.site.register(Entity)
admin.site.register(Activity)
admin.site.register(Album)
admin.site.register(Media)
