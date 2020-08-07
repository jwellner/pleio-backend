from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.lib import remove_none_from_dict
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE
from core.models import Comment

def resolve_edit_comment(_, info, input):
    # pylint: disable=redefined-builtin
    user = info.context["request"].user

    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        comment = Comment.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not comment.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    if 'description' in clean_input:
        comment.description = clean_input.get("description")
    if 'richDescription' in clean_input:
        comment.rich_description = clean_input.get("richDescription")

    comment.save()

    return {
        "entity": comment
    }
