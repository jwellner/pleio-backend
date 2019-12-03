from django.contrib.admin import AdminSite as BaseAdminSite
from reversion.admin import VersionAdmin

from core import config
from .models import User, Group, GroupMembership, Comment, Setting, Annotation, ProfileField
from file.models import FileFolder

class AdminSite(BaseAdminSite):
    site_header = 'Backend2'
    login_template = 'admin/oidc_login.html'


site = AdminSite(name='admin')


class UserAdmin(VersionAdmin):
    pass

class ProfileFieldAdmin(VersionAdmin):
    pass

class GroupAdmin(VersionAdmin):
    pass


class GroupMembershipAdmin(VersionAdmin):
    pass


class FileFolderAdmin(VersionAdmin):
    pass

class SettingAdmin(VersionAdmin):
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
