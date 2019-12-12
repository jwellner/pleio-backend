from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.models import Widget
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE
from core.lib import remove_none_from_dict

def resolve_edit_group_widget(_, info, input):
    # pylint: disable=redefined-builtin
    user = info.context.user
    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        widget = Widget.objects.get(id=clean_input.get('guid'))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not widget.group.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    if clean_input.get('settings'):
        widget.settings = clean_input.get('settings')
        widget.save()

    return {
        "entity": widget
    }
