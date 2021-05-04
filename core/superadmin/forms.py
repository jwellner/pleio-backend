from django import forms
from core import config
from core.resolvers.mutation_edit_site_setting import save_setting


def option_to_choice(option):
    return (option['value'], option['label'])


class LoginConfigForm(forms.Form):
    oidc_providers = forms.MultipleChoiceField(
        choices=map(option_to_choice, config.OIDC_PROVIDER_OPTIONS),
        error_messages={'required': 'Choose at least one option'})

    def save(self):
        data = self.cleaned_data

        save_setting('OIDC_PROVIDERS', data['oidc_providers'])
