from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE, USER_ROLES
from core.lib import clean_graphql_input
from core.resolvers import shared
from user.models import User


def resolve_edit_email_overview(_, info, input):
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

    if 'frequency' in clean_input:
        if clean_input.get('frequency') not in ['never', 'daily', 'weekly', 'monthly']:
            raise GraphQLError(COULD_NOT_SAVE)
        requested_user.profile.overview_email_interval = clean_input.get('frequency')

    if 'tags' in clean_input:
        requested_user.profile.overview_email_tags = clean_input.get("tags", [])

    if 'tagCategories' in clean_input:
        requested_user.profile.overview_email_categories = clean_input['tagCategories']

    requested_user.profile.save()

    return {
        "user": requested_user
    }
