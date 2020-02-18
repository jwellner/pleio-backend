from django.contrib.admin import ModelAdmin

from core import admin
from .models import Poll

class PollAdmin(ModelAdmin):
    pass


admin.site.register(Poll, PollAdmin)
