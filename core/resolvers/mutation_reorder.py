from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from core.models import Entity
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE
from core.lib import remove_none_from_dict
from cms.utils import reorder_positions

def resolve_reorder(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context["request"].user
    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        entity = Entity.objects.filter(~Q(page__isnull=True) | ~Q(wiki__isnull=True)).get_subclass(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not entity.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    if entity.parent and entity.parent.has_children():

        # check if positions are ordered and set position fields if not
        children = entity.parent.children.all()
        if len(list(set(children.values_list('position')))) == 1:
            position = 0
            for child in children:
                child.position = position
                child.save()
                position = position + 1
            # refetch for updated position
            entity = Entity.objects.filter(~Q(page__isnull=True) | ~Q(wiki__isnull=True)).get_subclass(id=clean_input.get("guid"))

        old_position = entity.position
        new_position = clean_input.get("destinationPosition")

        entity.position = new_position
        entity.save()

        reorder_positions(entity, old_position, new_position)

    return {
        "container": entity.parent
    }
