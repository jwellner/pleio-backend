from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.lib import clean_graphql_input
from core.constances import COULD_NOT_FIND, COULD_NOT_SAVE
from core.models import Comment
from core.resolvers import shared


def resolve_edit_comment(_, info, input):
    # pylint: disable=redefined-builtin
    user = info.context["request"].user

    clean_input = clean_graphql_input(input)

    shared.assert_authenticated(user)

    try:
        comment = Comment.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not comment.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    shared.resolve_update_rich_description(comment, clean_input)

    shared.update_updated_at(comment)
    comment.save()

    return {
        "entity": comment
    }
