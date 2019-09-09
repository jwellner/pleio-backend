import reversion
from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.lib import get_type, get_id
from core.constances import NOT_LOGGED_IN, INVALID_SUBTYPE, COULD_NOT_FIND, COULD_NOT_SAVE
from core.resolvers.shared import get_model_by_subtype
from core.resolvers.mutation_delete_comment import resolve_delete_comment

def resolve_delete_entity(_, info, input):
    # pylint: disable=redefined-builtin
    user = info.context.user

    subtype = get_type(input.get("guid"))
    entity_id = get_id(input.get("guid"))

    if subtype == "comment":
        return resolve_delete_comment(_, info, input)

    if not info.context.user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

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
        entity.delete()

        reversion.set_user(user)
        reversion.set_comment("editEntity mutation")

    return {
        'success': True
    }
