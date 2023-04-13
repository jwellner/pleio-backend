from core.resolvers import shared
from core.utils.entity import load_entity_by_id
from core.lib import get_access_id, clean_graphql_input, access_id_to_acl
from django.utils.translation import ugettext as _
from django.utils import timezone
from cms.models import Page


def create_copy(entity, user):
    # pylint: disable=redefined-builtin
    now = timezone.now()

    entity.owner = user
    entity.notifications_created = False
    entity.published = now
    entity.created_at = now
    entity.updated_at = now
    entity.update_last_action(entity.published)
    entity.read_access = access_id_to_acl(entity, get_access_id(entity.read_access))
    entity.write_access = access_id_to_acl(entity, 0)

    entity.title = _("Copy %s") % entity.title

    entity.pk = None
    entity.id = None
    entity.save()

    return entity


def resolve_copy_page(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context["request"].user
    page = load_entity_by_id(input['guid'], [Page])

    shared.assert_authenticated(user)
    shared.assert_write_access(page, user)

    entity = create_copy(page, user) 

    return {
        "entity": entity
    }

