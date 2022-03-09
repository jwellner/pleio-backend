from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.models import Entity
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE, USER_ROLES
from core.lib import clean_graphql_input

def resolve_toggle_entity_is_pinned(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context["request"].user
    clean_input = clean_graphql_input(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        entity = Entity.objects.get(id=clean_input.get('guid'))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not entity.group:
        raise GraphQLError(COULD_NOT_SAVE)

    if not user.has_role(USER_ROLES.ADMIN) and not (
            entity.group.members.filter(user=user, type__in=['admin', 'owner']).exists()
        ):
        raise GraphQLError(COULD_NOT_SAVE)

    entity.is_pinned = not entity.is_pinned
    entity.save()

    return {
        'success': True
    }
