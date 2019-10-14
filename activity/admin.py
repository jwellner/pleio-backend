from reversion.admin import VersionAdmin

from core import admin
from .models import StatusUpdate


class StatusUpdateAdmin(VersionAdmin):
    pass


admin.site.register(StatusUpdate, StatusUpdateAdmin)
