from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.lib import get_type, get_id, remove_none_from_dict
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, INVALID_SUBTYPE
from core.resolvers.shared import get_model_by_subtype
from core.models import Comment


def resolve_add_comment(_, info, input):
    # pylint: disable=redefined-builtin
    user = info.context.user

    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if clean_input.get("subtype") != "comment":
        raise GraphQLError(INVALID_SUBTYPE)

    if clean_input.get("containerGuid"):
        container_type = get_type(clean_input.get("containerGuid"))
        container_id = get_id(clean_input.get("containerGuid"))

        model = get_model_by_subtype(container_type)

        if not model:
            raise GraphQLError(INVALID_SUBTYPE)
      
        try:
            entity = model.objects.get(id=container_id)
        except ObjectDoesNotExist:
            raise GraphQLError(COULD_NOT_FIND)

        if entity.group and not entity.group.is_full_member(user) and not user.is_admin:
            raise GraphQLError("NOT_GROUP_MEMBER")
    else:
        raise GraphQLError("NO_CONTAINER_GUID")


    comment = Comment.objects.create(
        container=entity,
        owner=user,
        description=clean_input.get("description", "")
    )

    return {
        "entity": comment
    }
