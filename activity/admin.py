from django.contrib.admin import ModelAdmin

from core import admin
from .models import StatusUpdate


class StatusUpdateAdmin(ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = ('owner', 'created_at', 'short_description')

    def short_description(self, obj):
        return obj.description[:100]


admin.site.register(StatusUpdate, StatusUpdateAdmin)
