from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE, INVALID_VALUE, USER_ROLES
from core.models import UserProfileField, ProfileField
from user.models import User
from core.lib import remove_none_from_dict, access_id_to_acl, is_valid_json
from datetime import datetime

def validate_profile_field(string, field):
    if not isinstance(string, str):
        return False
    if field.field_type == 'html_field' and not is_valid_json(string):
        return False
    
    if not string == "":
        if field.field_type == 'select_field' and string not in field.field_options:
            return False
        if field.field_type == 'date_field':
            try:
                datetime.strptime(string, "%Y-%m-%d")
            except Exception:
                return False
        if field.field_type == 'multi_select_field':
            for selected in string.split(","):
                if selected not in field.field_options:
                    return False
    return True


def resolve_edit_profile_field(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context["request"].user
    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        requested_user = User.objects.get(id=clean_input.get('guid'))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not requested_user == user and not user.has_role(USER_ROLES.ADMIN):
        raise GraphQLError(COULD_NOT_SAVE)

    try:
        profile_field = ProfileField.objects.get(key=clean_input.get('key'))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    try:
        read_access = access_id_to_acl(requested_user, clean_input.get('accessId'))
    except Exception:
        raise GraphQLError(COULD_NOT_FIND)

    if not validate_profile_field(clean_input.get('value'), profile_field):
        raise GraphQLError(INVALID_VALUE)

    try:
        user_profile_field = UserProfileField.objects.get(user_profile=requested_user.profile, profile_field=profile_field)
        user_profile_field.read_access = read_access
        user_profile_field.value = clean_input.get('value')
        user_profile_field.save()
    except ObjectDoesNotExist:
        user_profile_field = UserProfileField.objects.create(user_profile=requested_user.profile, profile_field=profile_field, value=clean_input.get('value'),
                                                             read_access=read_access)

    return {
        "user": requested_user
    }
