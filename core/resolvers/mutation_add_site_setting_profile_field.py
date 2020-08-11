from graphql import GraphQLError
from core.models import ProfileField
from core.constances import NOT_LOGGED_IN, USER_NOT_SITE_ADMIN, COULD_NOT_SAVE
from core.lib import remove_none_from_dict

def resolve_add_site_setting_profile_field(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=unused-variable
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-locals

    user = info.context["request"].user
    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if not user.is_admin:
        raise GraphQLError(USER_NOT_SITE_ADMIN)

    profile_field, created = ProfileField.objects.get_or_create(key=clean_input['key'])

    if not created:
        raise GraphQLError(COULD_NOT_SAVE)

    if 'key' in clean_input:
        profile_field.key = clean_input["key"]

    if 'name' in clean_input:
        profile_field.name = clean_input["name"]

    if 'category' in clean_input:
        profile_field.category = clean_input["category"]

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

    if 'isHidden' in clean_input:
        profile_field.is_hidden = clean_input["isHidden"]

    profile_field.save()

    return {
        "profileItem": profile_field
    }
