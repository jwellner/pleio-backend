from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.lib import remove_none_from_dict, access_id_to_acl
from core.constances import NOT_LOGGED_IN, COULD_NOT_SAVE, COULD_NOT_FIND, INVALID_DATE
from core.utils.convert import tiptap_to_text
from cms.models import Page
from django.utils import dateparse


def resolve_add_page(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-branches

    user = info.context["request"].user

    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    entity = Page()

    if not entity.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    entity.owner = user
    entity.tags = clean_input.get("tags")

    if 'accessId' in clean_input:
        entity.read_access = access_id_to_acl(entity, clean_input.get("accessId"))
    else:
        entity.read_access = access_id_to_acl(entity, 0)
    entity.write_access = access_id_to_acl(entity, 0)

    if 'containerGuid' in clean_input:
        try:
            entity.parent = Page.objects.get(id=clean_input.get("containerGuid"))
        except ObjectDoesNotExist:
            raise GraphQLError(COULD_NOT_FIND)

    entity.title = clean_input.get("title")
    entity.rich_description = clean_input.get("richDescription")
    entity.description = tiptap_to_text(entity.rich_description)

    entity.page_type = clean_input.get("pageType")

    if 'timePublished' in clean_input:
        if clean_input.get("timePublished") is None:
            entity.published = None
        else:
            try:
                entity.published = dateparse.parse_datetime(clean_input.get("timePublished"))
            except ObjectDoesNotExist:
                raise GraphQLError(INVALID_DATE)

    entity.save()

    return {
        "entity": entity
    }
