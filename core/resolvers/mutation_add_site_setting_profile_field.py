from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from graphql import GraphQLError

from core.constances import COULD_NOT_FIND
from core.lib import clean_graphql_input, generate_code
from core.models import ProfileField, ProfileFieldValidator
from core.resolvers import shared


def create_profile_field(name):
    key = generate_code()
    try:
        return ProfileField.objects.create(key=key, name=name)
    except IntegrityError:
        create_profile_field(name=name)


def resolve_add_site_setting_profile_field(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=unused-variable
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-locals

    user = info.context["request"].user
    clean_input = clean_graphql_input(input)

    shared.assert_authenticated(user)

    shared.assert_administrator(user)

    profile_field = create_profile_field(clean_input["name"])

    resolve_update_field_type(profile_field, clean_input)
    resolve_update_field_options(profile_field, clean_input)
    resolve_update_profile_field_validator_id(profile_field, clean_input)
    
    shared.resolve_update_is_editable(profile_field, clean_input)
    shared.resolve_update_is_filter(profile_field, clean_input)
    shared.resolve_update_is_in_overview(profile_field, clean_input)
    shared.resolve_update_is_on_v_card(profile_field, clean_input)
    shared.resolve_update_is_in_onboarding(profile_field, clean_input)
    shared.resolve_update_is_mandatory(profile_field, clean_input)

    profile_field.save()

    return {
        "profileItem": profile_field
    }

def resolve_update_field_type(profile_field, clean_input):
    if 'fieldType' in clean_input:
        profile_field.field_type = clean_input["fieldType"]

def resolve_update_field_options(profile_field, clean_input):
    if 'fieldOptions' in clean_input:
        profile_field.field_options = clean_input["fieldOptions"]

def resolve_update_profile_field_validator_id(profile_field, clean_input):
    if 'profileFieldValidatorId' in clean_input:
        try:
            validator = ProfileFieldValidator.objects.get(id=clean_input.get('profileFieldValidatorId'))
            profile_field.validators.add(validator)
        except ObjectDoesNotExist:
            raise GraphQLError(COULD_NOT_FIND)
