from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.lib import remove_none_from_dict
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_ADD
from core.models import Comment, Entity, CommentMixin


def resolve_add_comment(_, info, input):
    # pylint: disable=redefined-builtin
    user = info.context["request"].user

    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if 'containerGuid' in clean_input:
        try:
            container = Entity.objects.get_subclass(id=clean_input.get("containerGuid"))
        except ObjectDoesNotExist:
            try:
                container = Comment.objects.get(id=clean_input.get("containerGuid"))
            except ObjectDoesNotExist:
                raise GraphQLError(COULD_NOT_FIND)

        if container.__class__ not in CommentMixin.__subclasses__():
            raise GraphQLError(COULD_NOT_ADD)
        
        if not container.can_comment(user):
            raise GraphQLError(COULD_NOT_ADD)

    else:
        raise GraphQLError("NO_CONTAINER_GUID")

    comment = Comment.objects.create(
        container=container,
        owner=user,
        description=clean_input.get("description", ""),
        rich_description=clean_input.get("richDescription")
    )

    return {
        "entity": comment
    }
