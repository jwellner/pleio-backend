from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.models import Group
from core.constances import COULD_NOT_FIND, USER_ROLES
from core.lib import clean_graphql_input
from core.resolvers import shared
from core.resolvers import group_shared


def resolve_edit_group(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements
    # pylint: disable=unused-variable

    user = info.context["request"].user

    clean_input = clean_graphql_input(input, [
        'defaultTags',
        'defaultTagCategories',
        'isAutoMembershipEnabled',
        'widgets',
    ])

    shared.assert_authenticated(user)

    try:
        group = Group.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    shared.assert_write_access(group, user)

    group_shared.update_name(group, clean_input)
    group_shared.update_icon(group, clean_input, image_owner=user)
    shared.update_featured_image(group, clean_input, image_owner=user)
    shared.resolve_update_rich_description(group, clean_input)
    shared.resolve_update_introduction(group, clean_input)
    shared.resolve_update_tags(group, clean_input)

    if 'defaultTags' in clean_input:
        group.content_presets['defaultTags'] = clean_input['defaultTags'] or []
    if 'defaultTagCategories' in clean_input:
        group.content_presets['defaultTagCategories'] = clean_input['defaultTagCategories'] or []

    group_shared.update_is_introduction_public(group, clean_input)
    group_shared.update_welcome_message(group, clean_input)
    group_shared.update_required_profile_fields_message(group, clean_input)
    group_shared.update_is_closed(group, clean_input)
    group_shared.update_is_membership_on_request(group, clean_input)
    group_shared.update_auto_notification(group, clean_input)
    group_shared.update_is_submit_updates_enabled(group, clean_input)
    group_shared.update_plugins(group, clean_input)
    group_shared.update_show_member_profile_fields(group, clean_input)
    group_shared.update_required_profile_fields(group, clean_input)
    group_shared.update_widgets(group, clean_input)

    if 'plugins' in clean_input:
        group.plugins = clean_input.get("plugins")

    if user.has_role(USER_ROLES.ADMIN):
        shared.update_is_featured(group, user, clean_input)
        group_shared.update_is_leaving_group_disabled(group, clean_input)
        group_shared.update_is_auto_membership_enabled(group, clean_input)
        group_shared.update_is_hidden(group, clean_input)

    shared.update_updated_at(group)

    group.save()

    return {
        "group": group
    }
