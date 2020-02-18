from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.lib import remove_none_from_dict
from core.constances import NOT_LOGGED_IN, COULD_NOT_SAVE, COULD_NOT_FIND
from cms.models import Page, Column
from cms.utils import reorder_positions


def resolve_add_column(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-branches
    # TODO: check if non admins can add page (roles)
    user = info.context.user

    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    old_position = None
    new_position = clean_input.get("position")
    column = Column()

    try:
        column.page = Page.objects.get(id=clean_input.get("containerGuid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not column.page.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    column.position = clean_input.get("position")
    column.parent_id = clean_input.get("parentGuid")
    column.width = clean_input.get("width")

    column.save()

    reorder_positions(column, old_position, new_position)

    return {
        "column": column
    }
