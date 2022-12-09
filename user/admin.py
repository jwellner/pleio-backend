from django.core.exceptions import PermissionDenied
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from user.models import User


def delete_selected(modeladmin, request, queryset):
    if not modeladmin.has_delete_permission(request):
        raise PermissionDenied
    for obj in queryset:
        obj.delete()


delete_selected.short_description = "Delete selected users"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    actions = [delete_selected]
    list_display = ('name', 'email', 'is_superadmin')
    list_filter = ['is_active']

    fieldsets = [
        (None, {'fields': ['email', 'name', 'password']}),
        ('Permissions', {'fields': ['is_active', 'is_superadmin']}),
    ]

    add_fieldsets = [
        (None, {
            'classes': ['wide'],
            'fields': ['email', 'name', 'password1', 'password2', 'is_superadmin'],
        }),
    ]

    search_fields = ['email']
    ordering = ['email']
    filter_horizontal = []

    def get_deleted_objects(self, objs, request):
        return [], {}, set(), []

    def delete_model(self, request, obj):
        obj.delete()
