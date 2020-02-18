from django.contrib.admin import ModelAdmin

from core import admin
from .models import Discussion


class DiscussionAdmin(ModelAdmin):
    pass


admin.site.register(Discussion, DiscussionAdmin)
