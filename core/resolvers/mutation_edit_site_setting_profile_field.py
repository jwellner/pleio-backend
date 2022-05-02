from graphql import GraphQLError
from core.models import ProfileField, ProfileFieldValidator
from core.constances import NOT_LOGGED_IN, USER_NOT_SITE_ADMIN, COULD_NOT_FIND, USER_ROLES, KEY_ALREADY_IN_USE
from core.lib import clean_graphql_input
from django.core.exceptions import ObjectDoesNotExist


def resolve_edit_site_setting_profile_field(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=unused-variable
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-locals

    user = info.context["request"].user
    clean_input = clean_graphql_input(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if not user.has_role(USER_ROLES.ADMIN):
        raise GraphQLError(USER_NOT_SITE_ADMIN)

    try:
        profile_field = ProfileField.objects.get(id=clean_input.get('guid'))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if 'name' in clean_input:
        profile_field.name = clean_input["name"]

    if 'key' in clean_input:
        key = clean_input["key"]
        if profile_field.key != key and ProfileField.objects.filter(key=key).first():
            raise GraphQLError(KEY_ALREADY_IN_USE)
        profile_field.key = key

    if 'isEditable' in clean_input:
        profile_field.is_editable_by_user = clean_input["isEditable"]

    if 'isFilter' in clean_input:
        profile_field.is_filter = clean_input["isFilter"]

    if 'isInOverview' in clean_input:
        profile_field.is_in_overview = clean_input["isInOverview"]

    if 'isOnVcard' in clean_input:
        profile_field.is_on_vcard = clean_input['isOnVcard']

    if 'fieldOptions' in clean_input:
        profile_field.field_options = [x for x in filter(lambda x: x, clean_input["fieldOptions"])]

    if 'isInOnboarding' in clean_input:
        profile_field.is_in_onboarding = clean_input["isInOnboarding"]

    if 'isMandatory' in clean_input:
        profile_field.is_mandatory = clean_input["isMandatory"]

    if 'profileFieldValidatorId' in input:
        if input.get('profileFieldValidatorId'):
            try:
                validator = ProfileFieldValidator.objects.get(id=clean_input.get('profileFieldValidatorId'))
                profile_field.validators.set([validator])
            except ObjectDoesNotExist:
                raise GraphQLError(COULD_NOT_FIND)
        else:
            profile_field.validators.set([])

    profile_field.save()

    return {
        "profileItem": profile_field
    }
