from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.models import Widget
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE
from core.lib import remove_none_from_dict
from cms.models import Page, Column
from cms.utils import reorder_positions


def resolve_add_widget(_, info, input):
    # pylint: disable=redefined-builtin
    user = info.context.user
    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        page = Page.objects.get(id=clean_input.get("containerGuid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not page.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    old_position = None
    new_position = clean_input.get("position")
    widget = Widget()

    try:
        widget.column = Column.objects.get(id=clean_input.get("parentGuid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    widget.page = page

    widget.position = clean_input.get("position")

    if 'settings' in clean_input:
        widget.settings = clean_input.get("settings")

    widget.type = clean_input.get("type")

    widget.save()

    reorder_positions(widget, old_position, new_position)

    return {
        "widget": widget
    }
