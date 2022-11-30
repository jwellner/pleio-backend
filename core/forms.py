# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import logging

from django.core.exceptions import ValidationError
from django.db.models import Q
from django import forms
from django.utils.translation import ugettext_lazy

from core import config
from core.models import ProfileField
from core.resolvers.shared import resolve_load_appointment_types

logger = logging.getLogger(__name__)


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
                    input_formats=('%d-%m-%Y',),
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


class MeetingsSettingsForm(forms.Form):
    onlineafspraken_enabled = forms.BooleanField(
        label="Enable onlineafspraken.nl", required=False)
    onlineafspraken_key = forms.CharField(
        label="Api key", required=False)
    onlineafspraken_secret = forms.CharField(
        label="Api secret", required=False)
    onlineafspraken_url = forms.CharField(
        label="Override default api url", required=False)
    videocall_appointment_type = forms.CharField(
        label="Configure appointment types",
        required=False,
        widget=forms.Textarea())

    videocall_enabled = forms.BooleanField(
        label="Enable videocalls", required=False)
    videocall_api_url = forms.CharField(
        label="Override api url", required=False)
    videocall_profilepage = forms.BooleanField(
        required=False,
        label="Enable videocalls at profile page")
    videocall_throttle = forms.IntegerField(
        label="Maximum number of room reservations per hour", required=False)

    @staticmethod
    def initial_values():
        return {
            'onlineafspraken_enabled': config.ONLINEAFSPRAKEN_ENABLED,
            'onlineafspraken_key': config.ONLINEAFSPRAKEN_KEY or '',
            'onlineafspraken_secret': config.ONLINEAFSPRAKEN_SECRET or '',
            'onlineafspraken_url': config.ONLINEAFSPRAKEN_URL or '',
            'videocall_appointment_type': MeetingsSettingsForm.load_appointment_type_config(),
            'videocall_enabled': config.VIDEOCALL_ENABLED,
            'videocall_api_url': config.VIDEOCALL_API_URL or '',
            'videocall_profilepage': config.VIDEOCALL_PROFILEPAGE or '',
            'videocall_throttle': config.VIDEOCALL_THROTTLE or 0,
        }

    @staticmethod
    def load_appointment_type_config():
        try:
            return json.dumps(resolve_load_appointment_types(), indent=2)
        except Exception:
            return '[]'

    def save(self):
        config.ONLINEAFSPRAKEN_ENABLED = bool(self.cleaned_data['onlineafspraken_enabled'])
        config.ONLINEAFSPRAKEN_KEY = self.cleaned_data['onlineafspraken_key'] or None
        config.ONLINEAFSPRAKEN_SECRET = self.cleaned_data['onlineafspraken_secret'] or None
        config.ONLINEAFSPRAKEN_URL = self.cleaned_data['onlineafspraken_url'] or None
        config.VIDEOCALL_APPOINTMENT_TYPE = self.cleaned_data['videocall_appointment_type'] or []
        config.VIDEOCALL_ENABLED = bool(self.cleaned_data['videocall_enabled'])
        config.VIDEOCALL_API_URL = self.cleaned_data['videocall_api_url'] or None
        config.VIDEOCALL_PROFILEPAGE = self.cleaned_data['videocall_profilepage'] or None

    def clean_videocall_appointment_type(self):
        try:
            return json.loads(self.cleaned_data['videocall_appointment_type'])
        except json.JSONDecodeError as e:
            raise ValidationError(str(e))


class ProfileSetForm(forms.Form):
    name = forms.CharField(
        label=ugettext_lazy("Name"),
        max_length=255,
        required=True)
    field = forms.ModelChoiceField(
        label=ugettext_lazy("Profile field"),
        queryset=ProfileField.objects.all(),
        widget=forms.Select,
    )

    @staticmethod
    def initial_values(profile_set):
        # pylint: disable=protected-access
        return {
            "name": profile_set.name or '',
            "field": profile_set.field.id if not profile_set._state.adding else None,
        }

    def save(self, profile_set):
        profile_set.name = self.cleaned_data['name']
        profile_set.field = self.cleaned_data['field']
        profile_set.save()
