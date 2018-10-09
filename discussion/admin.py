from reversion.admin import VersionAdmin

from core import admin
from .models import Discussion


class DiscussionAdmin(VersionAdmin):
    pass


admin.site.register(Discussion, DiscussionAdmin)
