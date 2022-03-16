from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.lib import clean_graphql_input, access_id_to_acl
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE
from cms.models import Page


def resolve_edit_page(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-branches

    user = info.context["request"].user

    clean_input = clean_graphql_input(input)

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

    if 'timePublished' in clean_input:
        entity.published = clean_input.get("timePublished", None)

    entity.save()

    return {
        "entity": entity
    }
