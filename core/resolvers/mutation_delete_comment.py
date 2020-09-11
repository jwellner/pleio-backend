from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.constances import COULD_NOT_FIND, COULD_NOT_SAVE, NOT_LOGGED_IN
from core.models import Comment

def resolve_delete_comment(_, info, input):
    # pylint: disable=redefined-builtin
    user = info.context["request"].user

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        comment = Comment.objects.get(id=input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not comment.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    comment.delete()

    return {
        'success': True
    }
