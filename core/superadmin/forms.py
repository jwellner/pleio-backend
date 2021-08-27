import django_filters

from django import forms
from core import config
from core.resolvers.mutation_edit_site_setting import save_setting
from file.models import ScanIncident


def option_to_choice(option):
    return (option['value'], option['label'])


class SettingsForm(forms.Form):
    oidc_providers = forms.MultipleChoiceField(
        choices=map(option_to_choice, config.OIDC_PROVIDER_OPTIONS),
        error_messages={'required': 'Choose at least one option'})

    edit_user_name_enabled = forms.BooleanField(required=False)

    def save(self):
        data = self.cleaned_data

        save_setting('OIDC_PROVIDERS', data['oidc_providers'])
        save_setting('EDIT_USER_NAME_ENABLED', data['edit_user_name_enabled'])


class ScanIncidentFilter(django_filters.FilterSet):
    blocked = django_filters.BooleanFilter(
        field_name='file',
        lookup_expr='isnull',
        widget=forms.Select(attrs={'class': 'form-select'}, choices=((None, "Alles"), (True, "Verwijderd",), (False, "Geblokkeerd"))),
    )

    class Meta:
        model = ScanIncident
        fields = []
