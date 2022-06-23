from django.core.exceptions import ObjectDoesNotExist
from graphql import GraphQLError

from cms.models import Page
from core.constances import COULD_NOT_FIND
from core.lib import access_id_to_acl, clean_graphql_input
from core.resolvers import shared


def resolve_add_page(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-branches

    user = info.context["request"].user
    entity = Page()

    clean_input = clean_graphql_input(input)
    
    shared.assert_authenticated(user)
    shared.assert_write_access(entity, user)
    
    entity.owner = user

    shared.resolve_update_tags(entity, clean_input)
    shared.resolve_update_title(entity, clean_input)
    shared.resolve_update_rich_description(entity, clean_input)
    shared.update_publication_dates(entity, clean_input)
    
    resolve_update_access(entity, clean_input)
    resolve_update_parent(entity, clean_input)
    resolve_update_page_type(entity, clean_input)

    entity.save()

    return {
        "entity": entity
    }

def resolve_update_page_type(entity, clean_input):
    entity.page_type = clean_input.get("pageType")

def resolve_update_parent(entity, clean_input):
    if 'containerGuid' in clean_input:
        try:
            entity.parent = Page.objects.get(id=clean_input.get("containerGuid"))
        except ObjectDoesNotExist:
            raise GraphQLError(COULD_NOT_FIND)

def resolve_update_access(entity, clean_input):
    if 'accessId' in clean_input:
        entity.read_access = access_id_to_acl(entity, clean_input.get("accessId"))
    else:
        entity.read_access = access_id_to_acl(entity, 0)
    entity.write_access = access_id_to_acl(entity, 0)
