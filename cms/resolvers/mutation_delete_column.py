import reversion
from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.constances import NOT_LOGGED_IN, COULD_NOT_SAVE, COULD_NOT_FIND
from cms.models import Column
from cms.utils import order_positions

def resolve_delete_column(_, info, input):
    # pylint: disable=redefined-builtin
    user = info.context.user

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        column = Column.objects.get(id=input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not column.page.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    with reversion.create_revision():
        parent_id = column.parent_id
        column.delete()

        reversion.set_user(user)
        reversion.set_comment("deleteColumn mutation")

        order_positions(parent_id)

    return {
        'success': True
    }
