from django.core.exceptions import ObjectDoesNotExist
from graphql import GraphQLError

from core.constances import COULD_NOT_FIND, COULD_NOT_SAVE, NOT_LOGGED_IN
from core.models import Entity

def resolve_archive_entity(_, info, guid):
    user = info.context["request"].user

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        entity = Entity.objects.get(id=guid)
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not entity.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    entity.is_archived = not entity.is_archived
    entity.save()

    return {
        'success': True
    }
