from django.contrib.admin import ModelAdmin

from core import admin
from .models import Question


class QuestionAdmin(ModelAdmin):
    pass


admin.site.register(Question, QuestionAdmin)
