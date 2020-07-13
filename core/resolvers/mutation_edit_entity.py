from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.lib import remove_none_from_dict, access_id_to_acl
from core.constances import NOT_LOGGED_IN, COULD_NOT_SAVE, INVALID_PARENT, COULD_NOT_FIND
from core.models import Entity
from core.resolvers.mutation_edit_comment import resolve_edit_comment
from file.models import FileFolder
from event.resolvers.mutation import resolve_edit_event
from discussion.resolvers.mutation import resolve_edit_discussion
from activity.resolvers.mutation import resolve_edit_status_update
from task.resolvers.mutation import resolve_edit_task

def resolve_edit_entity(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements

    user = info.context.user

    clean_input = remove_none_from_dict(input)

    if not info.context.user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        entity = Entity.objects.get_subclass(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        # TODO: update frontend to use editComment
        # raise GraphQLError(COULD_NOT_FIND)
        return resolve_edit_comment(_, info, input)

    if entity._meta.model_name == "event":
        return resolve_edit_event(_, info, input)

    if entity._meta.model_name == "discussion":
        return resolve_edit_discussion(_, info, input)

    if entity._meta.model_name == "statusupdate":
        return resolve_edit_status_update(_, info, input)

    if entity._meta.model_name == "task":
        return resolve_edit_task(_, info, input)

    if not entity.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    if 'tags' in clean_input:
        entity.tags = clean_input.get("tags")

    if 'accessId' in clean_input:
        entity.read_access = access_id_to_acl(entity, clean_input.get("accessId"))

    if 'writeAccessId' in clean_input:
        entity.write_access = access_id_to_acl(entity, clean_input.get("writeAccessId"))

    if entity._meta.model_name in ["blog", "news", "question", "wiki", "event"]:
        if 'title' in clean_input:
            entity.title = clean_input.get("title")
        if 'description' in clean_input:
            entity.description = clean_input.get("description")
        if 'richDescription' in clean_input:
            entity.rich_description = clean_input.get("richDescription")

    if entity._meta.model_name in ["blog", "news", "event"]:
        if 'featured' in clean_input:
            entity.featured_position_y = clean_input.get("featured").get("positionY", 0)
            entity.featured_video = clean_input.get("featured").get("video", None)
            if entity.featured_video:
                entity.featured_image = None
            elif clean_input.get("featured").get("image"):

                imageFile = FileFolder.objects.create(
                    owner=entity.owner,
                    upload=clean_input.get("featured").get("image"),
                    read_access=entity.read_access,
                    write_access=entity.write_access
                )

                entity.featured_image = imageFile

            entity.featured_position_y = clean_input.get("featured").get("positionY", 0)
        else:
            entity.featured_image = None
            entity.featured_position_y = 0
            entity.featured_video = None

    if entity._meta.model_name in ["blog"]:
        # TODO: subeditor may also set recommended
        if user.is_admin and 'isRecommended' in clean_input:
            entity.is_recommended = clean_input.get("isRecommended")

    if entity._meta.model_name in ["news"]:
        if 'isFeatured' in clean_input:
            entity.is_featured = clean_input.get("isFeatured")
        if 'source' in clean_input:
            entity.source = clean_input.get("source")

    if entity._meta.model_name in ["event"]:
        if 'isFeatured' in clean_input:
            entity.is_featured = clean_input.get("isFeatured")

    if entity._meta.model_name in ["wiki"]:
        if 'containerGuid' in clean_input:
            try:
                container = Entity.objects.get_subclass(id=clean_input.get("containerGuid"))
            except ObjectDoesNotExist:
                GraphQLError(COULD_NOT_FIND)
            if container._meta.model_name in ["wiki"]:
                entity.parent = container
            else:
                raise GraphQLError(INVALID_PARENT)

    entity.save()

    return {
        "entity": entity
    }
