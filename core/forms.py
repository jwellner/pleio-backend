# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db.models import Q
from django import forms
from django.utils.translation import ugettext_lazy
from core.models import ProfileField


class OnboardingForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(OnboardingForm, self).__init__(*args, **kwargs)

        self._profile_fields = []

        onboarding_fields = ProfileField.objects.filter(Q(is_in_onboarding=True) | Q(is_mandatory=True))

        for profile_field in onboarding_fields:

            if profile_field.field_type == "select_field":
                choices = [(value, value) for value in profile_field.field_options]
                self.fields[profile_field.guid] = forms.ChoiceField(
                    label=profile_field.name,
                    choices=choices,
                    required=profile_field.is_mandatory,
                    widget=forms.Select(attrs={'class': 'form__input'})
                )
            elif profile_field.field_type == "multi_select_field":
                choices = [(value, value) for value in profile_field.field_options]

                self.fields[profile_field.guid] = forms.MultipleChoiceField(
                    label=profile_field.name,
                    choices=choices,
                    required=profile_field.is_mandatory,
                    widget=forms.SelectMultiple(attrs={'class': 'form__input', 'size': '5', 'style': 'height:100px'})
                )
            elif profile_field.field_type == "date_field":

                self.fields[profile_field.guid] = forms.DateField(
                    label=profile_field.name,
                    required=profile_field.is_mandatory,
                    input_formats=('%d-%m-%Y', ),
                    widget=forms.DateInput(attrs={'class': 'form__input', 'placeholder': 'dd-mm-jjjj'},
                    format='%d-%m-%Y')
                )
            elif profile_field.field_type == "html_field":
                self.fields[profile_field.guid] = forms.CharField(
                    label=profile_field.name,
                    required=profile_field.is_mandatory,
                    widget=forms.Textarea(attrs={'class': 'form__input'})
                )
            else:
                self.fields[profile_field.guid] = forms.CharField(
                    label=profile_field.name,
                    required=profile_field.is_mandatory,
                    widget=forms.TextInput(attrs={'class': 'form__input'})
                )
            
            self._profile_fields.append(profile_field)

    def clean(self):
        cleaned_data = super().clean()
        for field in self._profile_fields:
            value = cleaned_data.get(field.guid)
            if not field.validate(value):
                self.add_error(field.guid, ugettext_lazy('Provide a valid value.'))

    @property
    def profile_fields(self):
        return self._profile_fields


class RequestAccessForm(forms.Form):

    request_access = forms.BooleanField(widget=forms.HiddenInput())


class EditEmailSettingsForm(forms.Form):

    INTERVALS = (
        ('never', ugettext_lazy('Never')),
        ('daily', ugettext_lazy('Daily')),
        ('weekly', ugettext_lazy('Weekly')),
        ('monthly', ugettext_lazy('Monthly'))
    )

    notifications_email_enabled = forms.BooleanField(required=False, label=ugettext_lazy('Receive notification emails'))
    overview_email_enabled = forms.ChoiceField(choices=INTERVALS, label=ugettext_lazy('Receive overview emails'))
