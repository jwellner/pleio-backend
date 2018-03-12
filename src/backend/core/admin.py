from django.contrib import admin
from .models import User, Group

class UserAdmin(admin.ModelAdmin):
    readonly_fields = ('external_id', 'last_login')
    list_display = ('name', 'email', 'is_active', 'last_login')
    exclude = ('password', )

admin.site.register(User, UserAdmin)
admin.site.register(Group)