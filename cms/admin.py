from reversion.admin import VersionAdmin

from core import admin
from .models import Page


class PageAdmin(VersionAdmin):
    pass


admin.site.register(Page, PageAdmin)
