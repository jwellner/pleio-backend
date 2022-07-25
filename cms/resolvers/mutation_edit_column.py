from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.lib import clean_graphql_input
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND
from cms.models import Column, Row
from cms.utils import reorder_positions
from core.resolvers import shared


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

    shared.assert_write_access(column.page, user)

    old_position = update_position(column, clean_input)

    update_row(column, clean_input)

    update_width(column, clean_input)

    column.save()

    reorder_positions(column, old_position, clean_input.get('position'))

    return {
        "column": column
    }


def update_position(column, clean_input):
    old_position = column.position

    if 'position' in clean_input:
        column.position = clean_input.get("position")

    return old_position


def update_row(column, clean_input):
    if 'parentGuid' in clean_input:
        try:
            column.row = Row.objects.get(id=clean_input.get("parentGuid"))
        except ObjectDoesNotExist:
            raise GraphQLError(COULD_NOT_FIND)


def update_width(column, clean_input):
    if 'width' in clean_input:
        column.width = clean_input.get("width")
