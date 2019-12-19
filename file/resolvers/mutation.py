import reversion
from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from ariadne import ObjectType
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_FIND_GROUP, COULD_NOT_SAVE
from core.lib import remove_none_from_dict, access_id_to_acl
from core.models import Group
from ..models import FileFolder


def update_access_recursive(user, entity, access_id, write_access_id):
    qs = FileFolder.objects.visible(user)
    qs = qs.filter(parent=entity)
    for file_folder in qs:
        if not file_folder.can_write(user):
            continue
        if access_id:
            file_folder.read_access = access_id_to_acl(file_folder, access_id)
        if write_access_id:
            file_folder.write_access = access_id_to_acl(file_folder, write_access_id)
        file_folder.save()
        update_access_recursive(user, file_folder, access_id, write_access_id)


mutation = ObjectType("Mutation")

@mutation.field("addFile")
def resolve_add_file(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context.user

    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    group = None
    parent = None

    if clean_input.get("containerGuid"):
        try:
            group = Group.objects.get(id=clean_input.get("containerGuid"))
        except ObjectDoesNotExist:
            try:
                parent = FileFolder.objects.get_subclass(id=clean_input.get("containerGuid"))
            except ObjectDoesNotExist:
                raise GraphQLError(COULD_NOT_FIND_GROUP)

    # get parent group
    if parent and parent.group:
        group = parent.group

    if group and not group.is_full_member(user) and not user.is_admin:
        raise GraphQLError("NOT_GROUP_MEMBER")

    with reversion.create_revision():
        entity = FileFolder()

        entity.owner = user
        entity.tags = clean_input.get("tags", [])

        if not clean_input.get("file"):
            raise GraphQLError("NO_FILE")

        entity.upload = clean_input.get("file")

        if parent:
            entity.parent = parent

        if group:
            entity.group = group

        entity.read_access = access_id_to_acl(entity, clean_input.get("accessId"))
        entity.write_access = access_id_to_acl(entity, clean_input.get("writeAccessId"))

        entity.save()

        reversion.set_user(user)
        reversion.set_comment("addFile mutation")

    return {
        "entity": entity
    }


def resolve_add_folder(_, info, input):
    """
    Used in core / addEntity
    """
    # pylint: disable=redefined-builtin

    user = info.context.user

    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    group = None
    parent = None

    if clean_input.get("containerGuid"):
        try:
            group = Group.objects.get(id=clean_input.get("containerGuid"))
        except ObjectDoesNotExist:
            try:
                parent = FileFolder.objects.get_subclass(id=clean_input.get("containerGuid"))
            except ObjectDoesNotExist:
                raise GraphQLError(COULD_NOT_FIND_GROUP)

    # get parent group
    if parent and parent.group:
        group = parent.group

    if group and not group.is_full_member(user) and not user.is_admin:
        raise GraphQLError("NOT_GROUP_MEMBER")

    with reversion.create_revision():
        entity = FileFolder()

        entity.owner = user
        entity.tags = clean_input.get("tags", [])
        entity.title = clean_input.get("title")
        entity.is_folder = True

        if parent:
            entity.parent = parent

        if group:
            entity.group = group

        entity.read_access = access_id_to_acl(entity, clean_input.get("accessId"))
        entity.write_access = access_id_to_acl(entity, clean_input.get("writeAccessId"))

        entity.save()

        reversion.set_user(user)
        reversion.set_comment("addEntity mutation")

    return {
        "entity": entity
    }

@mutation.field("editFileFolder")
def resolve_edit_file_folder(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context.user

    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        entity = FileFolder.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not entity.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    with reversion.create_revision():
        entity.owner = user

        if clean_input.get("title"):
            entity.title = clean_input.get("title")

        if clean_input.get("file"):
            entity.upload = clean_input.get("file")

        if clean_input.get("accessId"):
            entity.read_access = access_id_to_acl(entity, clean_input.get("accessId"))

        if clean_input.get("writeAccessId"):
            entity.write_access = access_id_to_acl(entity, clean_input.get("writeAccessId"))

        if entity.is_folder and clean_input.get("isAccessRecursive", False):
            update_access_recursive(user, entity, clean_input.get("accessId"), clean_input.get("writeAccessId"))

        entity.save()

        reversion.set_user(user)
        reversion.set_comment("editFileFolder mutation")

    return {
        "entity": entity
    }

@mutation.field("moveFileFolder")
def resolve_move_file_folder(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context.user

    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        entity = FileFolder.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not entity.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    group = None
    parent = None

    try:
        group = Group.objects.get(id=clean_input.get("containerGuid"))
    except ObjectDoesNotExist:
        try:
            parent = FileFolder.objects.get_subclass(id=clean_input.get("containerGuid"))
        except ObjectDoesNotExist:
            raise GraphQLError("invalid_new_container")


    with reversion.create_revision():
        if group:
            entity.group = group
            entity.parent = None

        if parent:
            entity.parent = parent

        entity.save()

        reversion.set_user(user)
        reversion.set_comment("editFileFolder mutation")

    return {
        "entity": entity
    }

@mutation.field("addImage")
def resolve_add_image(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context.user

    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    entity = FileFolder()

    entity.owner = user

    if not clean_input.get("image"):
        raise GraphQLError("NO_FILE")

    entity.upload = clean_input.get("image")

    entity.save()

    return {
        "file": entity
    }