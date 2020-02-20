from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.lib import remove_none_from_dict, access_id_to_acl
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE
from cms.models import Page


def resolve_edit_page(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-branches

    user = info.context.user

    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        entity = Page.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not entity.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    entity.tags = clean_input.get("tags")

    if clean_input.get("accessId") is not None:
        entity.read_access = access_id_to_acl(entity, clean_input.get("accessId"))

    entity.title = clean_input.get("title")
    entity.description = clean_input.get("description")
    entity.rich_description = clean_input.get("richDescription")

    entity.save()

    return {
        "entity": entity
    }
