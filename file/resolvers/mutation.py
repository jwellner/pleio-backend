from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from ariadne import ObjectType
from core import config
from core.constances import ACCESS_TYPE, NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE, USER_ROLES
from core.lib import clean_graphql_input, access_id_to_acl
from core.models import Group
from core.resolvers import shared
from user.models import User
from ..helpers.post_processing import ensure_correct_file_without_signals
from ..models import FileFolder, FILE_SCAN


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


def update_file_folder_owner(entity, owner, new_owner, recursive, full_recursive):
    current_owner_access = ACCESS_TYPE.user.format(entity.owner.guid)
    new_owner_access = ACCESS_TYPE.user.format(new_owner.guid)

    entity.owner = new_owner

    if current_owner_access in entity.write_access:
        new_write_access = [access for access in entity.write_access if not current_owner_access]
        new_write_access.append(new_owner_access)
        entity.write_access = new_write_access

    if current_owner_access in entity.read_access:
        new_read_access = [access for access in entity.read_access if not current_owner_access]
        new_read_access.append(new_owner_access)
        entity.read_access = new_read_access

    if recursive:
        child_filefolders = FileFolder.objects.filter(parent=entity)
        if not full_recursive:
            child_filefolders = child_filefolders.filter(owner=owner)
        for file_folder in child_filefolders:
            update_file_folder_owner(file_folder, owner, new_owner, recursive, full_recursive)
            file_folder.save()


mutation = ObjectType("Mutation")


@mutation.field("addFile")
def resolve_add_file(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context["request"].user

    clean_input = clean_graphql_input(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    group = None
    parent = None

    if 'containerGuid' in clean_input:
        try:
            group = Group.objects.get(id=clean_input.get("containerGuid"))
        except ObjectDoesNotExist:
            try:
                parent = FileFolder.objects.get_subclass(id=clean_input.get("containerGuid"))
                if not parent.can_write(user):
                    raise GraphQLError(COULD_NOT_SAVE)
            except ObjectDoesNotExist:
                if not clean_input.get("containerGuid") == user.guid:
                    raise GraphQLError("INVALID_CONTAINER_GUID")

    # get parent group
    if parent and parent.group:
        group = parent.group

    if group and not group.is_full_member(user) and not user.has_role(USER_ROLES.ADMIN):
        raise GraphQLError("NOT_GROUP_MEMBER")

    if not clean_input.get("file"):
        raise GraphQLError("NO_FILE")

    entity = FileFolder()

    entity.owner = user
    entity.tags = clean_input.get("tags", [])

    entity.upload = clean_input.get("file")

    if parent:
        entity.parent = parent

    if group:
        entity.group = group

    entity.read_access = access_id_to_acl(entity, clean_input.get("accessId", config.DEFAULT_ACCESS_ID))
    entity.write_access = access_id_to_acl(entity, clean_input.get("writeAccessId"))

    if 'richDescription' in clean_input:
        entity.rich_description = clean_input.get('richDescription')

    shared.update_publication_dates(entity, clean_input)

    if entity.scan() == FILE_SCAN.VIRUS:
        raise GraphQLError("INVALID_FILE")


    entity.save()

    ensure_correct_file_without_signals(entity)

    return {
        "entity": entity
    }


def resolve_add_folder(_, info, input):
    """
    Used in core / addEntity
    """
    # pylint: disable=redefined-builtin

    user = info.context["request"].user

    clean_input = clean_graphql_input(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    group = None
    parent = None

    if 'containerGuid' in clean_input:
        try:
            group = Group.objects.get(id=clean_input.get("containerGuid"))
        except ObjectDoesNotExist:
            try:
                parent = FileFolder.objects.get_subclass(id=clean_input.get("containerGuid"))
                if not parent.can_write(user):
                    raise GraphQLError(COULD_NOT_SAVE)
            except ObjectDoesNotExist:
                if not clean_input.get("containerGuid") == user.guid:
                    raise GraphQLError("INVALID_CONTAINER_GUID")

    # get parent group
    if parent and parent.group:
        group = parent.group

    if group and not group.is_full_member(user) and not user.has_role(USER_ROLES.ADMIN):
        raise GraphQLError("NOT_GROUP_MEMBER")

    entity = FileFolder()

    entity.owner = user
    entity.tags = clean_input.get("tags", [])
    entity.title = clean_input.get("title")
    entity.is_folder = True

    if 'richDescription' in clean_input:
        entity.rich_description = clean_input.get('richDescription')

    shared.update_publication_dates(entity, clean_input)

    if parent:
        entity.parent = parent

    if group:
        entity.group = group

    entity.read_access = access_id_to_acl(entity, clean_input.get("accessId"))
    entity.write_access = access_id_to_acl(entity, clean_input.get("writeAccessId"))

    entity.save()

    return {
        "entity": entity
    }


@mutation.field("editFileFolder")
def resolve_edit_file_folder(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context["request"].user

    clean_input = clean_graphql_input(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        entity = FileFolder.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not entity.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    if 'tags' in clean_input:
        entity.tags = clean_input.get("tags")

    if 'title' in clean_input and clean_input.get("title"):
        entity.title = clean_input.get("title")

    if 'richDescription' in clean_input:
        entity.rich_description = clean_input.get('richDescription')

    if 'file' in clean_input:
        entity.upload = clean_input.get("file")
        if entity.scan() == FILE_SCAN.VIRUS:
            raise GraphQLError("INVALID_FILE")

    shared.update_publication_dates(entity, clean_input)

    if 'accessId' in clean_input:
        entity.read_access = access_id_to_acl(entity, clean_input.get("accessId"))

    if 'writeAccessId' in clean_input:
        entity.write_access = access_id_to_acl(entity, clean_input.get("writeAccessId"))

    if entity.is_folder and clean_input.get("isAccessRecursive", False):
        update_access_recursive(user, entity, clean_input.get("accessId"), clean_input.get("writeAccessId"))

    if 'ownerGuid' in clean_input:
        update_file_folder_owner(entity, owner=entity.owner,
                                 new_owner=User.objects.get(id=clean_input['ownerGuid']),
                                 recursive='ownerGuidRecursive' in clean_input,
                                 full_recursive=clean_input.get('ownerGuidRecursive') == 'updateAllFiles')

    entity.save()

    ensure_correct_file_without_signals(entity)

    return {
        "entity": entity
    }


@mutation.field("moveFileFolder")
def resolve_move_file_folder(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context["request"].user

    clean_input = clean_graphql_input(input)

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
            if not clean_input.get("containerGuid") == user.guid:
                raise GraphQLError("INVALID_CONTAINER_GUID")

    if group:
        entity.group = group
        entity.parent = None

    if parent:
        # prevent moving folder in self or descendant of self
        parent_check = parent

        while parent_check:
            if parent_check == entity:
                raise GraphQLError("INVALID_CONTAINER_GUID")
            parent_check = parent_check.parent

        # entity already in parent
        if entity.parent == parent:
            raise GraphQLError("INVALID_CONTAINER_GUID")

        entity.parent = parent

    entity.save()

    return {
        "entity": entity
    }


@mutation.field("addImage")
def resolve_add_image(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context["request"].user

    clean_input = clean_graphql_input(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    entity = FileFolder()

    entity.owner = user

    if not clean_input.get("image"):
        raise GraphQLError("NO_FILE")

    entity.read_access = [ACCESS_TYPE.public]
    entity.write_access = access_id_to_acl(entity, 0)

    entity.upload = clean_input.get("image")

    if entity.scan() == FILE_SCAN.VIRUS:
        raise GraphQLError("INVALID_FILE")

    entity.save()

    return {
        "file": entity
    }
