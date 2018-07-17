from reversion.admin import VersionAdmin

from core import admin
from .models import Question

class QuestionAdmin(VersionAdmin):
    pass


admin.site.register(Question, QuestionAdmin)
