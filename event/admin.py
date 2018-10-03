from reversion.admin import VersionAdmin

from core import admin
from .models import Event


class EventAdmin(VersionAdmin):
    pass


admin.site.register(Event, EventAdmin)
