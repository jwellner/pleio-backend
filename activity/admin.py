from django.contrib.admin import ModelAdmin

from core import admin
from .models import StatusUpdate


class StatusUpdateAdmin(ModelAdmin):
    pass


admin.site.register(StatusUpdate, StatusUpdateAdmin)
