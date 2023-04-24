from typing import Union

from django.core.exceptions import ObjectDoesNotExist
from core.models import Entity, Group
from core.resolvers import shared
from core.resolvers.mutation_delete_comment import resolve_delete_comment
from core.utils.cleanup import schedule_cleanup_group_content_featured_images
from event.models import Event
from file.models import FileFolder
from file.resolvers.mutation import assert_not_referenced


def resolve_delete_entity(_, info, input):
    # pylint: disable=redefined-builtin
    user = info.context["request"].user

    shared.assert_authenticated(user)

    entity: Union[Entity, None]= None

    try:
        entity = Group.objects.get(id=input.get("guid"))
    except ObjectDoesNotExist:
        pass

    try:
        entity = Entity.objects.get_subclass(id=input.get("guid"))
    except ObjectDoesNotExist:
        pass

    if not entity:
        return resolve_delete_comment(_, info, input)

    shared.assert_write_access(entity, user)
    shared.update_updated_at(entity)

    if isinstance(entity, Group):
        schedule_cleanup_group_content_featured_images(entity)

    if isinstance(entity, FileFolder):
        entity.update_updated_at() # update parent folder dates
        if not input.get("force"):
            assert_not_referenced(entity)

    if isinstance(entity, Event):
        shared.resolve_pre_delete_event(entity)


    entity.delete()

    return {
        'success': True
    }
