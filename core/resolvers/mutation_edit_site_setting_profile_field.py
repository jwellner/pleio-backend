from django.core.exceptions import ObjectDoesNotExist
from graphql import GraphQLError

from core.constances import COULD_NOT_FIND, KEY_ALREADY_IN_USE, NOT_LOGGED_IN
from core.lib import clean_graphql_input
from core.models import ProfileField, ProfileFieldValidator
from core.resolvers import shared
from core.utils.entity import load_entity_by_id


def resolve_edit_site_setting_profile_field(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=unused-variable
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-locals

    user = info.context["request"].user
    clean_input = clean_graphql_input(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    shared.assert_administrator(user)

    profile_field = load_entity_by_id(input['guid'], [ProfileField])

    resolve_update_name(profile_field, clean_input)
    resolve_update_key(profile_field, clean_input)
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

def resolve_update_name(profile_field, clean_input):
    if 'name' in clean_input:
        profile_field.name = clean_input["name"]

def resolve_update_key(profile_field, clean_input):
    if 'key' in clean_input:
        key = clean_input["key"]
        if profile_field.key != key and ProfileField.objects.filter(key=key).first():
            raise GraphQLError(KEY_ALREADY_IN_USE)
        profile_field.key = key

def resolve_update_field_options(profile_field, clean_input):
    if 'fieldOptions' in clean_input:
        profile_field.field_options = [x for x in filter(lambda x: x, clean_input["fieldOptions"])]

def resolve_update_profile_field_validator_id(profile_field, clean_input):
    if 'profileFieldValidatorId' in clean_input:
        if clean_input.get('profileFieldValidatorId'):
            try:
                validator = ProfileFieldValidator.objects.get(id=clean_input.get('profileFieldValidatorId'))
                profile_field.validators.set([validator])
            except ObjectDoesNotExist:
                raise GraphQLError(COULD_NOT_FIND)
        else:
            profile_field.validators.set([])