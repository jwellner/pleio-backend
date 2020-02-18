from django.contrib.admin import ModelAdmin

from core import admin
from .models import Blog


class BlogAdmin(ModelAdmin):
    pass


admin.site.register(Blog, BlogAdmin)
