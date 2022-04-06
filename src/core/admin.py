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


class ShowroomObjectAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'type',
        'title',
        'subtext',
        'belongs_to',
        'source_repo',
        'date_created',
        'date_changed',
        'date_synced',
    )
    list_filter = ('type', 'source_repo')
    search_fields = ('title', 'subtext', 'source_repo_data')


admin.site.register(SourceRepository, SourceRepoAdmin)
admin.site.register(ShowroomObject, ShowroomObjectAdmin)
admin.site.register(ActivityDetail)
admin.site.register(EntityDetail)
admin.site.register(Media)
