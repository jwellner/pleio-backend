from django.contrib.admin import AdminSite as BaseAdminSite
from .models import User, Group, GroupMembership

class AdminSite(BaseAdminSite):
    site_header = 'Backend2'
    login_template = 'admin/oidc_login.html'


site = AdminSite(name='admin')
site.register(User)
site.register(Group)
site.register(GroupMembership)