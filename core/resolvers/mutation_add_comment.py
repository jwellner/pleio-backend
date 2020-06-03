from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.lib import remove_none_from_dict
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND
from core.models import Comment, Entity


def resolve_add_comment(_, info, input):
    # pylint: disable=redefined-builtin
    user = info.context.user

    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if 'containerGuid' in clean_input:
        try:
            entity = Entity.objects.get_subclass(id=clean_input.get("containerGuid"))
        except ObjectDoesNotExist:
            raise GraphQLError(COULD_NOT_FIND)

        if entity.group and not entity.group.is_full_member(user) and not user.is_admin:
            raise GraphQLError("NOT_GROUP_MEMBER")
    else:
        raise GraphQLError("NO_CONTAINER_GUID")

    comment = Comment.objects.create(
        container=entity,
        owner=user,
        description=clean_input.get("description", ""),
        rich_description=clean_input.get("richDescription")
    )

    return {
        "entity": comment
    }
