from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.lib import remove_none_from_dict
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE
from cms.models import Row
from cms.utils import reorder_positions


def resolve_edit_row(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-branches

    user = info.context["request"].user

    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        row = Row.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not row.page.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    old_position = row.position
    new_position = clean_input.get("position")

    if 'position' in clean_input:
        row.position = clean_input.get("position")

    if 'isFullWidth' in clean_input:
        row.is_full_width = clean_input.get("isFullWidth")

    row.save()

    reorder_positions(row, old_position, new_position)

    return {
        "row": row
    }
