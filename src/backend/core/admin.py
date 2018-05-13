from django.contrib import admin
from .models import User, Group, GroupMembership

admin.site.register(User)
admin.site.register(Group)
admin.site.register(GroupMembership)