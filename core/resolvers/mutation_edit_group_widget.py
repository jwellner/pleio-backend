from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.models import Widget
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE
from core.lib import clean_graphql_input
from cms.utils import reorder_positions

def resolve_edit_group_widget(_, info, input):
    # pylint: disable=redefined-builtin
    user = info.context["request"].user
    clean_input = clean_graphql_input(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        widget = Widget.objects.get(id=clean_input.get('guid'))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not widget.group.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    old_position = widget.position
    new_position = clean_input.get("position")

    if 'position' in clean_input:
        old_position = widget.position
        new_position = clean_input.get("position")
        widget.position = clean_input.get('position')
        widget.save()
        reorder_positions(widget, old_position, new_position)

    if 'settings' in clean_input:
        widget.settings = clean_input.get('settings')
        widget.save()

    return {
        "entity": widget
    }
