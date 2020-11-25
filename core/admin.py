from django.contrib import messages
from django.contrib.admin import AdminSite as BaseAdminSite, ModelAdmin
from django.shortcuts import render

from core import config
from core.lib import tenant_schema
from core.models import Group, GroupMembership, Comment, Setting, Annotation, ProfileField, UserProfile
from core.tasks import elasticsearch_rebuild
from user.models import User
from file.models import FileFolder

class AdminSite(BaseAdminSite):
    site_header = 'Backend2'
    login_template = 'admin/oidc_login.html'

    def get_urls(self):
        # pylint: disable=import-outside-toplevel
        from django.urls import path
        urls = super().get_urls()
        urls += [
            path('tasks/', self.admin_view(self.task_view))
        ]
        return urls

    def task_view(self, request):
        context = {}
        if request.method == 'POST':
            messages.add_message(request, messages.INFO, 'Search index rebuild is started in the background.')
            elasticsearch_rebuild.delay(tenant_schema())
        return render(request, 'admin/tasks.html', context)


site = AdminSite(name='admin')


def remove_user_data(self, request, queryset):
    # pylint: disable=unused-argument
    for user in queryset.all():
        user.delete()


remove_user_data.short_description = "Remove user with profile data"

class UserAdmin(ModelAdmin):
    actions =  [remove_user_data]

    def get_actions(self, request):
        # pylint: disable=unused-argument
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

class UserProfileAdmin(ModelAdmin):
    pass

class ProfileFieldAdmin(ModelAdmin):
    pass

class GroupAdmin(ModelAdmin):
    pass


class GroupMembershipAdmin(ModelAdmin):
    pass


class FileFolderAdmin(ModelAdmin):
    pass

class SettingAdmin(ModelAdmin):
    readonly_fields = ('key', )

    """Overwrite save_model to use core.config"""
    def save_model(self, request, obj, form, change):
        # pylint: disable=unused-argument
        setattr(config, obj.key, obj.value)


site.register(User, UserAdmin)
site.register(UserProfile, UserProfileAdmin)
site.register(ProfileField, ProfileFieldAdmin)
site.register(Group, GroupAdmin)
site.register(GroupMembership, GroupMembershipAdmin)
site.register(Comment)
site.register(FileFolder, FileFolderAdmin)
site.register(Setting, SettingAdmin)
site.register(Annotation)
