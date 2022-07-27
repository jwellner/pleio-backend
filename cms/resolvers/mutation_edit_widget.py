from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.lib import clean_graphql_input
from core.constances import COULD_NOT_FIND
from core.models import Widget
from cms.models import Column
from cms.utils import reorder_positions
from core.resolvers import shared


def resolve_edit_widget(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-branches

    user = info.context["request"].user

    clean_input = clean_graphql_input(input)

    shared.assert_authenticated(user)

    try:
        widget = Widget.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    shared.assert_write_access(widget.page, user)

    old_position = update_position(widget, clean_input)
    update_column(widget, clean_input)
    update_settings(widget, clean_input)

    widget.save()

    reorder_positions(widget, old_position, clean_input.get("position"))

    return {
        "widget": widget
    }


def update_position(widget, clean_input):
    old_position = widget.position
    if 'position' in clean_input:
        widget.position = clean_input.get("position")
    return old_position


def update_column(widget, clean_input):
    if 'parentGuid' in clean_input:
        try:
            widget.column = Column.objects.get(id=clean_input.get("parentGuid"))
        except ObjectDoesNotExist:
            raise GraphQLError(COULD_NOT_FIND)


def update_settings(widget, clean_input):
    if 'settings' in clean_input:
        widget.settings = clean_input.get("settings")
