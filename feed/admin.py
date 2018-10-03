from reversion.admin import VersionAdmin

from core import admin
from .models import Feed


class FeedAdmin(VersionAdmin):
    pass


admin.site.register(Feed, FeedAdmin)
