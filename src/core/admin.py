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
        'showroom_id',
        'type',
        'title',
        'subtext',
        'belongs_to',
        'source_repo',
        'date_created',
        'date_changed',
        'date_synced',
        'active',
    )
    list_filter = ('type', 'source_repo', 'active')
    search_fields = (
        'title',
        'subtext',
        'source_repo_data',
        'id',
        'source_repo_object_id',
        'source_repo_owner_id',
    )


class ActivityDetailAdmin(admin.ModelAdmin):
    list_display = (
        'showroom_id',
        'title',
        'activity_type_label',
        'keywords',
        'has_featured_medium',
    )
    search_fields = (
        'showroom_object__id',
        'showroom_object__title',
        'activity_type',
        'keywords',
    )

    def showroom_id(self, obj):
        return obj.showroom_object.showroom_id

    def title(self, obj):
        return obj.showroom_object.title

    def activity_type_label(self, obj):
        if not obj.activity_type or type(obj.activity_type) is not dict:
            return None
        label = obj.activity_type.get('label')
        return label

    def has_featured_medium(self, obj):
        return True if obj.featured_medium else False


class EntityDetailAdmin(admin.ModelAdmin):
    list_display = (
        'showroom_id',
        'title',
        'expertise',
        'photo',
    )
    search_fields = (
        'showroom_object__id',
        'showroom_object__title',
        'expertise',
    )

    def showroom_id(self, obj):
        return obj.showroom_object.showroom_id

    def title(self, obj):
        return obj.showroom_object.title


admin.site.register(SourceRepository, SourceRepoAdmin)
admin.site.register(ShowroomObject, ShowroomObjectAdmin)
admin.site.register(ActivityDetail, ActivityDetailAdmin)
admin.site.register(EntityDetail, EntityDetailAdmin)
admin.site.register(Media)
