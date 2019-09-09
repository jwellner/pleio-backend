from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.lib import get_type, get_id
from core.constances import INVALID_SUBTYPE, COULD_NOT_FIND, COULD_NOT_SAVE
from core.models import Comment

def resolve_delete_comment(_, info, input):
    # pylint: disable=redefined-builtin
    user = info.context.user

    subtype = get_type(input.get("guid"))
    entity_id = get_id(input.get("guid"))

    if subtype != "comment":
        raise GraphQLError(INVALID_SUBTYPE)

    try:
        comment = Comment.objects.get(id=entity_id)
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not comment.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)
    
    comment.delete()

    return {
        'success': True
    }
