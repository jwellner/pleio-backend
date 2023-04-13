from django.utils.translation import ugettext as _
from django.utils import timezone

from core.resolvers import shared
from core.utils.entity import load_entity_by_id
from core.lib import get_access_id, clean_graphql_input, access_id_to_acl
from event.models import Event


def copy_event(event_id, user, parent=None):
    # pylint: disable=redefined-builtin

    entity = Event.objects.get(id=event_id)

    now = timezone.now()

    # preserve time of original event
    if entity.start_date:
        difference = None
        if entity.end_date:
            difference = entity.end_date - entity.start_date
        entity.start_date = entity.start_date.replace(
            year=now.year,
            month=now.month,
            day=now.day,
        )
        if entity.end_date:
            entity.end_date = entity.start_date + difference

    entity.owner = user
    entity.is_featured = False
    entity.is_pinned = False
    entity.notifications_created = False
    entity.published = None
    entity.created_at = now
    entity.updated_at = now
    entity.update_last_action(entity.published)
    entity.read_access = access_id_to_acl(entity, get_access_id(entity.read_access))
    entity.write_access = access_id_to_acl(entity, 0)

    if parent:
        entity.parent = parent

    # subevents keep original title
    if not parent:
        entity.title = _("Copy %s") % entity.title

    entity.pk = None
    entity.id = None
    entity.save()

    return entity


def resolve_copy_event(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context["request"].user
    event = load_entity_by_id(input['guid'], [Event])

    clean_input = clean_graphql_input(input)

    shared.assert_authenticated(user)
    shared.assert_write_access(event, user)

    entity = copy_event(clean_input.get("guid"), user)

    resolve_copy_subevents(entity, event, user, clean_input)

    return {
        "entity": entity
    }


# Content property resolvers:
def resolve_copy_subevents(entity, event, user, clean_input):
    if clean_input.get("copySubevents", True) and event.has_children():
        for child in event.children.all():
            copy_event(child.guid, user, entity)
