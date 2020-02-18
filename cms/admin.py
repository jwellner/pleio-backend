from django.contrib.admin import ModelAdmin

from core import admin
from .models import Page


class PageAdmin(ModelAdmin):
    pass


admin.site.register(Page, PageAdmin)
