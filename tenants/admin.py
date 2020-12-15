from django.contrib import admin

from tenants.models import Client, Domain
from user.models import User

class DomainInline(admin.TabularInline):
    model = Domain


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    inlines = [DomainInline]
    list_display = ('schema_name', 'primary_domain', 'elgg_database')


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    pass
