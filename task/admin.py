from django.contrib.admin import ModelAdmin

from core import admin
from .models import Task


class TaskAdmin(ModelAdmin):
    pass


admin.site.register(Task, TaskAdmin)
