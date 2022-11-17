from django.contrib import admin

from tenants.models import Client, Domain, Agreement, AgreementVersion, AgreementAccept
from user.models import User


class DomainInline(admin.TabularInline):
    model = Domain


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    inlines = [DomainInline]
    list_display = ('schema_name', 'primary_domain')


@admin.register(Agreement)
class AgreementAdmin(admin.ModelAdmin):
    pass


@admin.register(AgreementVersion)
class AgreementVersionAdmin(admin.ModelAdmin):
    readonly_fields = ("slug", "created_at")


@admin.register(AgreementAccept)
class AgreementAcceptAdmin(admin.ModelAdmin):
    pass


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    pass
