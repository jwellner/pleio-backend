from reversion.admin import VersionAdmin

from core import admin
from .models import Blog


class BlogAdmin(VersionAdmin):
    pass


admin.site.register(Blog, BlogAdmin)
