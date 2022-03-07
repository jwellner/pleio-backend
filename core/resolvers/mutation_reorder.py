from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from core.models import Entity
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE
from core.lib import clean_graphql_input

def resolve_reorder(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context["request"].user
    clean_input = clean_graphql_input(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        entity = Entity.objects.filter(~Q(page__isnull=True) | ~Q(wiki__isnull=True)).get_subclass(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not entity.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    if entity.parent and entity.parent.has_children():

        children = list(entity.parent.children.all())

        current_index = children.index(entity)
        children.insert(clean_input.get("destinationPosition"), children.pop(current_index))

        for index, child in enumerate(children):
            if child.position != index:
                child.position = index
                child.save()

        entity.refresh_from_db()

    return {
        "container": entity.parent
    }
