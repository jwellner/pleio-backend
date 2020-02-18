from django.contrib.admin import AdminSite as BaseAdminSite, ModelAdmin

from core import config
from core.models import Group, GroupMembership, Comment, Setting, Annotation, ProfileField
from user.models import User
from file.models import FileFolder

class AdminSite(BaseAdminSite):
    site_header = 'Backend2'
    login_template = 'admin/oidc_login.html'


site = AdminSite(name='admin')


class UserAdmin(ModelAdmin):
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
        setattr(config, obj.key, obj.value)


site.register(User, UserAdmin)
site.register(ProfileField, ProfileFieldAdmin)
site.register(Group, GroupAdmin)
site.register(GroupMembership, GroupMembershipAdmin)
site.register(Comment)
site.register(FileFolder, FileFolderAdmin)
site.register(Setting, SettingAdmin)
site.register(Annotation)
