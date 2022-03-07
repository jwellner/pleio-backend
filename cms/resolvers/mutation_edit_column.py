from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.lib import clean_graphql_input
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE
from cms.models import Column, Row
from cms.utils import reorder_positions


def resolve_edit_column(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-branches

    user = info.context["request"].user

    clean_input = clean_graphql_input(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        column = Column.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not column.page.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    old_position = column.position
    new_position = clean_input.get("position")

    if 'position' in clean_input:
        column.position = clean_input.get("position")

    if 'parentGuid' in clean_input:
        try:
            column.row = Row.objects.get(id=clean_input.get("parentGuid"))
        except ObjectDoesNotExist:
            raise GraphQLError(COULD_NOT_FIND)

    if 'width' in clean_input:
        column.is_full_width = clean_input.get("width")

    column.save()

    reorder_positions(column, old_position, new_position)

    return {
        "column": column
    }
