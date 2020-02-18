from django.contrib.admin import ModelAdmin

from core import admin
from .models import Wiki


class WikiAdmin(ModelAdmin):
    pass


admin.site.register(Wiki, WikiAdmin)
