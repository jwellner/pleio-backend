from ariadne import ObjectType
from core import config
from core.models import ProfileField, Group
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND
from graphql import GraphQLError

from core.utils.filter_options import get_filter_options

filters = ObjectType("Filters")


@filters.field("users")
def resolve_users_filters(_, info, groupGuid=None):
    # pylint: disable=unused-argument
    user_filters = []

    user = info.context["request"].user

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    group = None

    if groupGuid:
        try:
            group = Group.objects.get(id=groupGuid)
        except Group.DoesNotExist:
            raise GraphQLError(COULD_NOT_FIND)

    # only get configured profile fields
    profile_section_guids = []

    for section in config.PROFILE_SECTIONS:
        profile_section_guids.extend(section['profileFieldGuids'])

    profile_fields = ProfileField.objects.filter(id__in=profile_section_guids)

    for field in profile_fields:
        if group:
            is_filter = group.profile_field_settings.filter(show_field=True, profile_field=field).exists()
        else:
            is_filter = field.is_filter

        if is_filter and field.is_filterable:
            if not group and field.field_type in ['multi_select_field', 'select_field']:
                options = field.field_options
            else:
                options = get_filter_options(field.key, user, group)
            if options:
                user_filters.append({
                    "name": field.key,
                    "fieldType": field.field_type,
                    "label": field.name,
                    "keys": options
                })

    return user_filters
