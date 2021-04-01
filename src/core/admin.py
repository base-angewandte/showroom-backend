from django.contrib import admin

from .models import Activity, Album, Entity, Media, SourceRepository


class SourceRepoAdmin(admin.ModelAdmin):
    list_display = ('repo_label', 'url_repository', 'id', 'api_key')

    def repo_label(self, obj):
        return obj.label_institution + ' : ' + obj.label_repository

    repo_label.short_description = 'Source repository'


admin.site.register(SourceRepository, SourceRepoAdmin)
admin.site.register(Entity)
admin.site.register(Activity)
admin.site.register(Album)
admin.site.register(Media)
