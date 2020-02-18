from django.contrib.admin import ModelAdmin

from core import admin
from .models import Event


class EventAdmin(ModelAdmin):
    pass


admin.site.register(Event, EventAdmin)
