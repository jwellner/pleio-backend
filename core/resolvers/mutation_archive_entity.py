from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from graphql import GraphQLError

from core.constances import COULD_NOT_FIND, COULD_NOT_SAVE, NOT_LOGGED_IN
from core.models import Entity
from core.resolvers import shared


def resolve_archive_entity(_, info, guid):
    user = info.context["request"].user

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        entity = Entity.objects.get_subclass(id=guid)
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not entity.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    revision = shared.resolve_start_revision(entity, user)

    resolve_toggle_is_archived(entity)
    entity.save()

    shared.store_update_revision(revision, entity)

    return {
        'success': True
    }


def resolve_toggle_is_archived(entity):
    entity.is_archived = not entity.is_archived
    if entity.is_archived:
        entity.schedule_archive_after = timezone.now()
    else:
        entity.schedule_archive_after = None
