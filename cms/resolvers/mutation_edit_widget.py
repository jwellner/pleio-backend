from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.lib import remove_none_from_dict
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE
from core.models import Widget
from cms.models import Column
from cms.utils import reorder_positions


def resolve_edit_widget(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-branches

    user = info.context.user

    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        widget = Widget.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not widget.page.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    old_position = widget.position
    new_position = clean_input.get("position")

    if clean_input.get("position"):
        widget.position = clean_input.get("position")
    if clean_input.get("parentGuid"):
        try:
            widget.column = Column.objects.get(id=clean_input.get("parentGuid"))
        except ObjectDoesNotExist:
            raise GraphQLError(COULD_NOT_FIND)
    if clean_input.get("settings"):
        widget.is_full_width = clean_input.get("settings")

    widget.save()

    reorder_positions(widget, old_position, new_position)

    return {
        "widget": widget
    }
