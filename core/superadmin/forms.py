import django_filters
from auditlog.models import LogEntry

from django import forms
from django.contrib.contenttypes.models import ContentType
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from core import config
from core.constances import OIDC_PROVIDER_OPTIONS
from core.models.agreement import CustomAgreement
from file.models import ScanIncident


def option_to_choice(option):
    return (option['value'], option['label'])


class SettingsForm(forms.Form):
    oidc_providers = forms.MultipleChoiceField(
        choices=map(option_to_choice, OIDC_PROVIDER_OPTIONS),
        error_messages={'required': 'Choose at least one option'})

    custom_javascript = forms.CharField(required=False)
    csp_header_exceptions = forms.CharField(required=False)

    def clean(self):
        cleaned_data = super().clean()
        url_validator = URLValidator(schemes=["http", "https"])
        for url in cleaned_data['csp_header_exceptions'].splitlines(False):
            try:
                url_validator(url)
            except ValidationError:
                self.add_error('csp_header_exceptions', "Contains invalid URL")

    def save(self):
        data = self.cleaned_data

        config.OIDC_PROVIDERS = data['oidc_providers']
        config.CUSTOM_JAVASCRIPT = data['custom_javascript']
        config.CSP_HEADER_EXCEPTIONS = data['csp_header_exceptions'].splitlines(False)


class ScanIncidentFilter(django_filters.FilterSet):
    blocked = django_filters.BooleanFilter(
        field_name='file',
        lookup_expr='isnull',
        widget=forms.Select(attrs={'class': 'form-select'}, choices=((None, "Alles"), (True, "Verwijderd",), (False, "Geblokkeerd"))),
    )
    filename = django_filters.CharFilter(
        field_name='file_title',
        lookup_expr='icontains',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _("Filename")})
    )

    class Meta:
        model = ScanIncident
        fields = []


class AuditLogFilter(django_filters.FilterSet):
    object_pk = django_filters.CharFilter(
        lookup_expr='iexact',
        widget=forms.TextInput(attrs={'placeholder': 'Object ID'}),
    )

    content_type = django_filters.ModelChoiceFilter(queryset=ContentType.objects.all().order_by('app_label'))

    class Meta:
        model = LogEntry
        fields = []


class CustomAgreementForm(forms.ModelForm):
    class Meta:
        model = CustomAgreement
        fields = ['name', 'document']


class OptionalFeaturesForm(forms.Form):
    collab_editing_enabled = forms.BooleanField(required=False)
    edit_user_name_enabled = forms.BooleanField(required=False)
    push_notifications_enabled = forms.BooleanField(required=False)
    datahub_external_content_enabled = forms.BooleanField(required=False)
    recurring_events_enabled = forms.BooleanField(required=False)
    event_add_email_attendee = forms.CharField(required=False)

    def save(self):
        data = self.cleaned_data
        config.COLLAB_EDITING_ENABLED = bool(data['collab_editing_enabled'])
        config.EDIT_USER_NAME_ENABLED = bool(data['edit_user_name_enabled'])
        config.PUSH_NOTIFICATIONS_ENABLED = bool(data['push_notifications_enabled'])
        config.DATAHUB_EXTERNAL_CONTENT_ENABLED = bool(data['datahub_external_content_enabled'])
        config.RECURRING_EVENTS_ENABLED = bool(data['recurring_events_enabled'])
        config.EVENT_ADD_EMAIL_ATTENDEE = data['event_add_email_attendee']


class SupportContractForm(forms.Form):
    site_plan = forms.CharField(required=False)
    support_contract_enabled = forms.BooleanField(required=False)
    support_contract_hours_remaining = forms.FloatField(required=False)

    def save(self):
        data = self.cleaned_data
        config.SITE_PLAN = data['site_plan']
        config.SUPPORT_CONTRACT_ENABLED = data['support_contract_enabled']
        config.SUPPORT_CONTRACT_HOURS_REMAINING = data['support_contract_hours_remaining']
