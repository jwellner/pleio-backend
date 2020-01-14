import reversion
from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.lib import remove_none_from_dict
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE
from cms.models import Column
from cms.utils import reorder_positions


def resolve_edit_column(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-branches

    user = info.context.user

    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        column = Column.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not column.page.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    with reversion.create_revision():
        old_position = column.position
        new_position = clean_input.get("position")

        if clean_input.get("position"):
            column.position = clean_input.get("position")
        if clean_input.get("parentGuid"):
            column.parent_id = clean_input.get("parentGuid")
        if clean_input.get("width"):
            column.is_full_width = clean_input.get("width")

        column.save()

        reversion.set_user(user)
        reversion.set_comment("editColumn mutation")

        reorder_positions(column, old_position, new_position)

    return {
        "column": column
    }
