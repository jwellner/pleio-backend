from graphql import GraphQLError
from django.db import IntegrityError
from core.models import ProfileField, ProfileFieldValidator
from core.constances import NOT_LOGGED_IN, USER_NOT_SITE_ADMIN, USER_ROLES, COULD_NOT_FIND
from core.lib import remove_none_from_dict, generate_code
from django.core.exceptions import ObjectDoesNotExist

def create_profile_field():
    key = generate_code()
    try:
        return ProfileField.objects.create(key=key)
    except IntegrityError:
        create_profile_field()


def resolve_add_site_setting_profile_field(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=unused-variable
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-locals

    user = info.context["request"].user
    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if not user.has_role(USER_ROLES.ADMIN):
        raise GraphQLError(USER_NOT_SITE_ADMIN)

    profile_field = create_profile_field()

    if 'name' in clean_input:
        profile_field.name = clean_input["name"]

    if 'isEditable' in clean_input:
        profile_field.is_editable_by_user = clean_input["isEditable"]

    if 'isFilter' in clean_input:
        profile_field.is_filter = clean_input["isFilter"]

    if 'isInOverview' in clean_input:
        profile_field.is_in_overview = clean_input["isInOverview"]

    if 'fieldType' in clean_input:
        profile_field.field_type = clean_input["fieldType"]

    if 'fieldOptions' in clean_input:
        profile_field.field_options = clean_input["fieldOptions"]

    if 'isInOnboarding' in clean_input:
        profile_field.is_in_onboarding = clean_input["isInOnboarding"]

    if 'isMandatory' in clean_input:
        profile_field.is_mandatory = clean_input["isMandatory"]

    if 'profileFieldValidatorId' in clean_input:
        try:
            validator = ProfileFieldValidator.objects.get(id=clean_input.get('profileFieldValidatorId'))
            profile_field.validators.add(validator)
        except ObjectDoesNotExist:
            raise GraphQLError(COULD_NOT_FIND)

    profile_field.save()

    return {
        "profileItem": profile_field
    }
