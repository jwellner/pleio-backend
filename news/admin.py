from django.contrib.admin import ModelAdmin

from core import admin
from .models import News


class NewsAdmin(ModelAdmin):
    pass


admin.site.register(News, NewsAdmin)
