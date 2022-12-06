import validators
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django import forms

from tenants.models import Client, Domain

# from django-tenants
SQL_IDENTIFIER_RE = re.compile(r'^[_a-zA-Z0-9]{1,63}$')
SQL_SCHEMA_NAME_RESERVED_RE = re.compile(r'^pg_', re.IGNORECASE)


def validate_domain(value):
    exists = Domain.objects.filter(domain=value).first()
    if exists:
        raise ValidationError("Domain already exists")
    if not validators.domain(value):
        raise ValidationError("Invalid domain")


def validate_schema(value):
    valid = SQL_IDENTIFIER_RE.match(value) and not SQL_SCHEMA_NAME_RESERVED_RE.match(value)
    if not valid:
        raise ValidationError("Invalid schema name")


class AddSiteForm(forms.Form):
    schema_name = forms.CharField(label='Schema', max_length=100, required=True, validators=[validate_schema])
    domain = forms.CharField(label='Domain', max_length=250, required=True, validators=[validate_domain])
    backup = forms.CharField(label='From backup', max_length=250, required=False)

    def clean(self):
        cleaned_data = super().clean()

        schema_name = cleaned_data.get("schema_name")

        exists = Client.objects.filter(schema_name=schema_name).first()
        if exists:
            self.add_error('schema_name', "Schema name already exists")


class DeleteSiteForm(forms.Form):
    site_id = forms.IntegerField(widget=forms.HiddenInput())
    check = forms.CharField(label='Re-type the schema name to delete', max_length=255, required=True)

    def clean(self):
        cleaned_data = super().clean()

        site_id = cleaned_data.get("site_id")
        check = cleaned_data.get("check")

        site = Client.objects.filter(id=site_id).first()
        if not site.schema_name == check:
            self.add_error('check', "Type schema name to delete this site")


class ConfirmSiteForm(forms.Form):
    site_id = forms.IntegerField(widget=forms.HiddenInput())


class ConfirmSiteBackupForm(ConfirmSiteForm):
    include_files = forms.BooleanField(initial=True,
                                       required=False,
                                       label=_("Include files"),
                                       widget=forms.CheckboxInput())
    create_archive = forms.BooleanField(initial=False,
                                        required=False,
                                        label=_("Create zip-file"),
                                        widget=forms.CheckboxInput())


class SearchUserForm(forms.Form):
    email = forms.CharField(label='Email', max_length=255, required=True)


class AgreementAddForm(forms.Form):
    name = forms.CharField(label='Name', max_length=255, required=True)


class AgreementAddVersionForm(forms.Form):
    agreement_id = forms.IntegerField(widget=forms.HiddenInput())

    version = forms.CharField(label='Version', max_length=255, required=True)
    document = forms.FileField(label='Document', required=True, widget=forms.FileInput(attrs={'accept': 'application/pdf'}))
