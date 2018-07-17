from reversion.admin import VersionAdmin

from core import admin
from .models import News

class NewsAdmin(VersionAdmin):
    pass


admin.site.register(News, NewsAdmin)
