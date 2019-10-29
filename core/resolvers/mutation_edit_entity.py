import reversion
from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.lib import remove_none_from_dict, access_id_to_acl
from core.constances import NOT_LOGGED_IN, COULD_NOT_SAVE
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

    with reversion.create_revision():

        entity.tags = clean_input.get("tags", [])

        entity.read_access = access_id_to_acl(entity, clean_input.get("accessId", 0))
        entity.write_access = access_id_to_acl(entity, clean_input.get("writeAccessId", 0))

        if entity._meta.model_name in ["blog", "news", "question", "wiki", "event"]:
            entity.title = clean_input.get("title")
            entity.description = clean_input.get("description", "")
            entity.rich_description = clean_input.get("richDescription")

        if entity._meta.model_name in ["blog", "news", "event"]:
            if clean_input.get("featured"):
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
            if user.is_admin:
                entity.is_recommended = clean_input.get("isRecommended")

        if entity._meta.model_name in ["news"]:
            entity.is_featured = clean_input.get("isFeatured", False)
            entity.source = clean_input.get("source", "")

        if entity._meta.model_name in ["event"]:
            entity.is_featured = clean_input.get("isFeatured", False)


        entity.save()

        reversion.set_user(user)
        reversion.set_comment("editEntity mutation")

    return {
        "entity": entity
    }
