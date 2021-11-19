from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from django.utils import dateparse
from core.lib import remove_none_from_dict, access_id_to_acl
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE, INVALID_DATE
from core.utils.convert import tiptap_to_text
from cms.models import Page


def resolve_edit_page(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-branches

    user = info.context["request"].user

    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        entity = Page.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not entity.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    if 'tags' in clean_input:
        entity.tags = clean_input.get("tags")

    if 'accessId' in clean_input:
        entity.read_access = access_id_to_acl(entity, clean_input.get("accessId"))

    if 'title' in clean_input:
        entity.title = clean_input.get("title")

    if 'richDescription' in clean_input:
        entity.rich_description = clean_input.get("richDescription")
        entity.description = tiptap_to_text(entity.rich_description)

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
