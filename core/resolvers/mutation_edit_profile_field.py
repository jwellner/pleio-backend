from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE, USER_ROLES, INVALID_VALUE
from core.models import UserProfileField, ProfileField
from user.models import User
from core.lib import clean_graphql_input, access_id_to_acl, is_valid_json
from core.resolvers.scalar import secure_prosemirror_value_parser
from datetime import datetime

def validate_profile_field(value, field):
    if not isinstance(value, str):
        return False

    if field.field_type == 'html_field':
        if not is_valid_json(value):
            raise ValidationError(f"Invalid JSON")

        secure_prosemirror_value_parser(value)
    
    if not value == "":
        if field.field_type == 'select_field' and value not in field.field_options:
            raise ValidationError(f"Value is not in field options")
        if field.field_type == 'date_field':
            try:
                datetime.strptime(value, "%Y-%m-%d")
            except Exception:
                raise ValidationError(f"Invalid date format expecting Y-m-d")

        if field.field_type == 'multi_select_field':
            for selected in value.split(","):
                if selected not in field.field_options:
                    raise ValidationError(f"Selected option is not in field options")

    # run trough field validators
    if not field.validate(value):
        raise ValidationError(f"Custom field validator error")

    return value


def resolve_edit_profile_field(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context["request"].user
    clean_input = clean_graphql_input(input)

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
        write_access = access_id_to_acl(requested_user, 0)
    except Exception:
        raise GraphQLError(COULD_NOT_FIND)

    try:
        validate_profile_field(clean_input.get('value'), profile_field)
    except ValidationError:
        # TODO: not sure is frontend is ready for custom errors
        raise GraphQLError(INVALID_VALUE)


    user_profile_field, created = UserProfileField.objects.get_or_create(user_profile=requested_user.profile, profile_field=profile_field)
    user_profile_field.read_access = read_access
    if created:
        user_profile_field.write_access = write_access
    user_profile_field.value = clean_input.get('value')
    user_profile_field.save()
    
    return {
        "user": requested_user
    }
