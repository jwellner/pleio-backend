from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.constances import NOT_LOGGED_IN, COULD_NOT_SAVE
from core.models import Entity, Group
from core.resolvers.mutation_delete_comment import resolve_delete_comment
from core.utils.cleanup import schedule_cleanup_group_content_featured_images


def resolve_delete_entities(_, info, input):
    # pylint: disable=redefined-builtin
    user = info.context["request"].user

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    guids = input.get("guids")

    entity = None

    for guid in guids:
        try:
            entity = Group.objects.get(id=guid)
        except ObjectDoesNotExist:
            pass

        try:
            entity = Entity.objects.get_subclass(id=guid)
        except ObjectDoesNotExist:
            continue

        if not entity.can_write(user):
            raise GraphQLError(COULD_NOT_SAVE)

        if isinstance(entity, Group):
            schedule_cleanup_group_content_featured_images(entity)

        entity.delete()


    return {
        'success': True
    }
