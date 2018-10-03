from reversion.admin import VersionAdmin

from core import admin
from .models import Wiki


class WikiAdmin(VersionAdmin):
    pass


admin.site.register(Wiki, WikiAdmin)
