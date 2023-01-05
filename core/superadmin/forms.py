from core.models.agreement import CustomAgreement
import django_filters

from auditlog.models import LogEntry
from django import forms
from django.contrib.contenttypes.models import ContentType
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from core import config
from core.constances import OIDC_PROVIDER_OPTIONS
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

    def save(self):
        data = self.cleaned_data
        config.COLLAB_EDITING_ENABLED = data['collab_editing_enabled']
        config.EDIT_USER_NAME_ENABLED = data['edit_user_name_enabled']
        config.PUSH_NOTIFICATIONS_ENABLED = data['push_notifications_enabled']

class SupportContractForm(forms.Form):
    support_contract_enabled = forms.BooleanField(required=False)
    support_contract_hours_remaining = forms.FloatField(required=False)

    def save(self):
        data = self.cleaned_data
        config.SUPPORT_CONTRACT_ENABLED = data['support_contract_enabled']
        config.SUPPORT_CONTRACT_HOURS_REMAINING = data['support_contract_hours_remaining']
