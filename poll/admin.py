from reversion.admin import VersionAdmin

from core import admin
from .models import Poll

class PollAdmin(VersionAdmin):
    pass


admin.site.register(Poll, PollAdmin)
