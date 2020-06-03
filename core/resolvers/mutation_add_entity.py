from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.lib import remove_none_from_dict, get_model_by_subtype, access_id_to_acl
from core.constances import NOT_LOGGED_IN, INVALID_SUBTYPE, COULD_NOT_FIND_GROUP
from core.models import Group, Entity
from core.resolvers.mutation_add_comment import resolve_add_comment
from file.models import FileFolder
from event.resolvers.mutation import resolve_add_event
from discussion.resolvers.mutation import resolve_add_discussion
from activity.resolvers.mutation import resolve_add_status_update
from task.resolvers.mutation import resolve_add_task
from file.resolvers.mutation import resolve_add_folder


def resolve_add_entity(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-branches
    # TODO: check if non admins can add news (roles)

    user = info.context.user

    clean_input = remove_none_from_dict(input)

    if clean_input.get("subtype") == "comment":
        return resolve_add_comment(_, info, input)
    if clean_input.get("subtype") == "event":
        return resolve_add_event(_, info, input)
    if clean_input.get("subtype") == "discussion":
        return resolve_add_discussion(_, info, input)
    if clean_input.get("subtype") in ["status_update", "thewire"]:
        return resolve_add_status_update(_, info, input)
    if clean_input.get("subtype") == "task":
        return resolve_add_task(_, info, input)
    if clean_input.get("subtype") == "folder":
        return resolve_add_folder(_, info, input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    model = get_model_by_subtype(clean_input.get("subtype"))

    if not model:
        raise GraphQLError(INVALID_SUBTYPE)

    group = None
    parent = None

    # containerGuid can be parent objects for some subtypes
    # TODO: should we refactor this in backend 2 to use parentGuid?
    if 'containerGuid' in clean_input and clean_input.get("subtype") in ["wiki"]:
        try:
            group = Group.objects.get(id=clean_input.get("containerGuid"))
        except ObjectDoesNotExist:
            try:
                parent = Entity.objects.get_subclass(id=clean_input.get("containerGuid"))

            except ObjectDoesNotExist:
                raise GraphQLError(COULD_NOT_FIND_GROUP)

    elif 'containerGuid' in clean_input:
        try:
            group = Group.objects.get(id=clean_input.get("containerGuid"))
        except ObjectDoesNotExist:
            raise GraphQLError(COULD_NOT_FIND_GROUP)

    if parent and parent.group:
        group = parent.group

    if group and not group.is_full_member(user) and not user.is_admin:
        raise GraphQLError("NOT_GROUP_MEMBER")

    # default fields for all entities
    entity = model()

    entity.owner = user
    entity.tags = clean_input.get("tags")

    if group:
        entity.group = group

    entity.read_access = access_id_to_acl(entity, clean_input.get("accessId"))
    entity.write_access = access_id_to_acl(entity, clean_input.get("writeAccessId"))

    if clean_input.get("subtype") in ["blog", "news", "question", "wiki"]:
        entity.title = clean_input.get("title")
        entity.description = clean_input.get("description")
        entity.rich_description = clean_input.get("richDescription")

    if clean_input.get("subtype") in ["blog", "news"]:
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

    if clean_input.get("subtype") in ["blog"]:
        # TODO: subeditor may also set recommended
        if user.is_admin:
            entity.is_recommended = clean_input.get("isRecommended")

    if clean_input.get("subtype") in ["news"]:
        entity.is_featured = clean_input.get("isFeatured", False)
        entity.source = clean_input.get("source", "")

    if clean_input.get("subtype") in ["wiki"]:
        entity.parent = parent

    entity.save()
    if clean_input.get("subtype") in ["blog", "news", "question"]:
        entity.add_follow(user)

    return {
        "entity": entity
    }
