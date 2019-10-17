from reversion.admin import VersionAdmin

from core import admin
from .models import Task


class TaskAdmin(VersionAdmin):
    pass


admin.site.register(Task, TaskAdmin)
