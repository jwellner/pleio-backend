from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.constances import NOT_LOGGED_IN, COULD_NOT_SAVE, COULD_NOT_FIND
from cms.models import Row
from cms.utils import order_positions

def resolve_delete_row(_, info, input):
    # pylint: disable=redefined-builtin
    user = info.context.user

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        row = Row.objects.get(id=input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not row.page.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    parent_id = row.parent_id
    row.delete()

    order_positions(parent_id)

    return {
        'success': True
    }
