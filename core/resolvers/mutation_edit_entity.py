import reversion
from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.lib import get_type, get_id, remove_none_from_dict
from core.constances import NOT_LOGGED_IN, COULD_NOT_SAVE, COULD_NOT_FIND, INVALID_SUBTYPE
from core.resolvers.shared import get_model_by_subtype, access_id_to_acl


def resolve_edit_entity(_, info, input):
    # pylint: disable=redefined-builtin
    user = info.context.user

    clean_input = remove_none_from_dict(input)

    if not info.context.user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    subtype = get_type(clean_input.get("guid"))
    entity_id = get_id(clean_input.get("guid"))

    model = get_model_by_subtype(subtype)

    if not model:
        raise GraphQLError(INVALID_SUBTYPE)

    try:
        entity = model.objects.get(id=entity_id)
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not entity.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    with reversion.create_revision():
        entity.title = clean_input.get("title")
        entity.description = clean_input.get("description", "")
        entity.tags = clean_input.get("tags", [])

        entity.read_access = access_id_to_acl(entity, clean_input.get("accessId"))

        entity.save()

        reversion.set_user(user)
        reversion.set_comment("editEntity mutation")

    return {
        "entity": entity
    }
