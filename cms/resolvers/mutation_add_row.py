from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.lib import clean_graphql_input
from core.constances import NOT_LOGGED_IN, COULD_NOT_SAVE, COULD_NOT_FIND
from cms.models import Page, Row
from cms.utils import reorder_positions


def resolve_add_row(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-branches
    # TODO: check if non admins can add page (roles)
    user = info.context["request"].user

    clean_input = clean_graphql_input(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    old_position = None
    new_position = clean_input.get("position")
    row = Row()

    try:
        row.page = Page.objects.get(id=clean_input.get("containerGuid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not row.page.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    row.position = clean_input.get("position")
    row.is_full_width = clean_input.get("isFullWidth")

    row.save()

    reorder_positions(row, old_position, new_position)

    return {
        "row": row
    }
