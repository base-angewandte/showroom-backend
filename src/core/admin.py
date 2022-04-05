from django.contrib import admin

from .models import (
    ActivityDetail,
    EntityDetail,
    Media,
    ShowroomObject,
    SourceRepository,
)


class SourceRepoAdmin(admin.ModelAdmin):
    list_display = ('repo_label', 'url_repository', 'id', 'api_key')

    def repo_label(self, obj):
        return obj.label_institution + ' : ' + obj.label_repository

    repo_label.short_description = 'Source repository'


admin.site.register(SourceRepository, SourceRepoAdmin)
admin.site.register(ShowroomObject)
admin.site.register(ActivityDetail)
admin.site.register(EntityDetail)
admin.site.register(Media)
