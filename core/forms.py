# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime
from django import forms
from core import config
from core.models import ProfileField, UserProfileField
from django.core.exceptions import ObjectDoesNotExist

class OnboardingForm(forms.Form):

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(OnboardingForm, self).__init__(*args, **kwargs)

        self._profile_fields = []

        profile_sections = config.PROFILE_SECTIONS
        for section in profile_sections:
            for guid in section['profileFieldGuids']:
                profile_field = ProfileField.objects.get(id=guid)

                if profile_field.is_mandatory or profile_field.is_in_onboarding:
                    value = None
                    try:
                        user_profile_field = UserProfileField.objects.get(profile_field=profile_field, user_profile=user.profile)
                        value = user_profile_field.value
                    except ObjectDoesNotExist:
                        pass

                    if profile_field.field_type == "select_field":
                        choices = [(value, value) for value in profile_field.field_options]
                        self.fields[profile_field.name] = forms.ChoiceField(
                            initial=value,
                            choices=choices,
                            required=profile_field.is_mandatory,
                            widget=forms.Select(attrs={'class': 'form__input'})
                        )
                    elif profile_field.field_type == "multi_select_field":
                        choices = [(value, value) for value in profile_field.field_options]
                        if value:
                            values = value.split(',')
                        else:
                            values = []
                        self.fields[profile_field.name] = forms.MultipleChoiceField(
                            initial=values,
                            choices=choices,
                            required=profile_field.is_mandatory,
                            widget=forms.SelectMultiple(attrs={'class': 'form__input', 'size': '5', 'style': 'height:100px'})
                        )
                    elif profile_field.field_type == "date_field":
                        # date is stored in format YYYY-mm-dd
                        if value:
                            date = datetime.strptime(value, '%Y-%m-%d')
                            value = date.strftime('%d-%m-%Y')

                        self.fields[profile_field.name] = forms.DateField(
                            initial=value,
                            required=profile_field.is_mandatory,
                            input_formats=('%d-%m-%Y', ),
                            widget=forms.DateInput(attrs={'class': 'form__input', 'placeholder': 'dd-mm-jjjj'},
                            format='%d-%m-%Y')
                        )
                    elif profile_field.field_type == "html_field":
                        self.fields[profile_field.name] = forms.CharField(
                            initial=value,
                            required=profile_field.is_mandatory,
                            widget=forms.Textarea(attrs={'class': 'form__input'})
                        )
                    else:
                        self.fields[profile_field.name] = forms.CharField(
                            initial=value,
                            required=profile_field.is_mandatory,
                            widget=forms.TextInput(attrs={'class': 'form__input'})
                        )
                    
                    self._profile_fields.append(profile_field)

    @property
    def profile_fields(self):
        return self._profile_fields
