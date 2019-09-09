from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.lib import get_type, get_id, remove_none_from_dict
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, INVALID_SUBTYPE, COULD_NOT_SAVE
from core.models import Comment

def resolve_edit_comment(_, info, input):
    # pylint: disable=redefined-builtin
    user = info.context.user

    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    subtype = get_type(clean_input.get("guid"))
    comment_id = get_id(clean_input.get("guid"))

    if subtype != "comment":
        raise GraphQLError(INVALID_SUBTYPE)

    try:
        comment = Comment.objects.get(id=comment_id)
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not comment.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    comment.description = clean_input.get("description", "")
    comment.rich_description = clean_input.get("richDescription")

    comment.save()

    return {
        "entity": comment
    }
