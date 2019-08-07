import reversion
from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.lib import get_type, get_id, remove_none_from_dict
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, INVALID_SUBTYPE, ACCESS_TYPE
from core.resolvers.shared import get_model_by_subtype, access_id_to_acl
from core.models import Group


def resolve_add_entity(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context.user

    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    model = get_model_by_subtype(clean_input.get("subtype"))

    if not model:
        raise GraphQLError(INVALID_SUBTYPE)

    group = None

    if clean_input.get("containerGuid"):
        container_type = get_type(clean_input.get("containerGuid"))
        container_id = get_id(clean_input.get("containerGuid"))

        if not container_type == "group":
            raise GraphQLError("INVALID_CONTAINER_SUBTYPE")
        
        try:
            group = Group.objects.get(id=container_id)
        except ObjectDoesNotExist:
            raise GraphQLError(COULD_NOT_FIND)

        if not group.is_full_member(user) and not user.is_admin:
            raise GraphQLError("NOT_GROUP_MEMBER")

    with reversion.create_revision():
        # default fiels
        entity = model()
        entity.title = clean_input.get("title")
        entity.description = clean_input.get("description")
        entity.owner = user
        entity.tags = clean_input.get("tags")

        if group:
            entity.group = group

        entity.read_access = access_id_to_acl(entity, clean_input.get("accessId"))
        entity.write_access = [ACCESS_TYPE.user.format(user.id)]

        entity.save()

        reversion.set_user(user)
        reversion.set_comment("addEntity mutation")

    return {
        "entity": entity
    }
