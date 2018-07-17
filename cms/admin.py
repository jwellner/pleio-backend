from reversion.admin import VersionAdmin

from core import admin
from .models import CmsPage

class CmsPageAdmin(VersionAdmin):
    pass


admin.site.register(CmsPage, CmsPageAdmin)
