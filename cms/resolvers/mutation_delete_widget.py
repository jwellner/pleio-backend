from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.constances import NOT_LOGGED_IN, COULD_NOT_SAVE, COULD_NOT_FIND
from core.models import Widget
from cms.utils import order_positions

def resolve_delete_widget(_, info, input):
    # pylint: disable=redefined-builtin
    user = info.context.user

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        widget = Widget.objects.get(id=input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not widget.page.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    column = widget.column
    widget.delete()

    order_positions(column)

    return {
        'success': True
    }
