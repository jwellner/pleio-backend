from django.contrib.admin import AdminSite as BaseAdminSite
from reversion.admin import VersionAdmin

from .models import User, Group, GroupMembership, Comment, FileFolder


class AdminSite(BaseAdminSite):
    site_header = 'Backend2'
    login_template = 'admin/oidc_login.html'


site = AdminSite(name='admin')


class UserAdmin(VersionAdmin):
    pass


class GroupAdmin(VersionAdmin):
    pass


class GroupMembershipAdmin(VersionAdmin):
    pass


class FileFolderAdmin(VersionAdmin):
    pass


site.register(User, UserAdmin)
site.register(Group, GroupAdmin)
site.register(GroupMembership, GroupMembershipAdmin)
site.register(Comment)
site.register(FileFolder, FileFolderAdmin)
