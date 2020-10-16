from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.lib import remove_none_from_dict, access_id_to_acl, tenant_schema
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND_GROUP, COULD_NOT_ADD, USER_NOT_MEMBER_OF_GROUP, COULD_NOT_FIND, COULD_NOT_SAVE, USER_ROLES
from core.models import Group
from news.models import News
from file.models import FileFolder
from file.tasks import resize_featured

def resolve_add_news(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-branches

    user = info.context["request"].user

    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if not (user.has_role(USER_ROLES.ADMIN) or user.has_role(USER_ROLES.EDITOR)):
        raise GraphQLError(COULD_NOT_ADD)

    group = None

    if 'containerGuid' in clean_input:
        try:
            group = Group.objects.get(id=clean_input.get("containerGuid"))
        except ObjectDoesNotExist:
            raise GraphQLError(COULD_NOT_FIND_GROUP)

    if group and not group.is_full_member(user) and not user.has_role(USER_ROLES.ADMIN):
        raise GraphQLError(USER_NOT_MEMBER_OF_GROUP)

    entity = News()

    entity.owner = user
    entity.tags = clean_input.get("tags")

    entity.group = group

    entity.read_access = access_id_to_acl(entity, clean_input.get("accessId"))
    entity.write_access = access_id_to_acl(entity, clean_input.get("writeAccessId"))

    entity.title = clean_input.get("title")
    entity.description = clean_input.get("description")
    entity.rich_description = clean_input.get("richDescription")

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

            resize_featured.delay(tenant_schema(), imageFile.guid)

            entity.featured_image = imageFile

        entity.featured_position_y = clean_input.get("featured").get("positionY", 0)
    else:
        entity.featured_image = None
        entity.featured_position_y = 0
        entity.featured_video = None

    if user.has_role(USER_ROLES.ADMIN) or user.has_role(USER_ROLES.EDITOR):
        entity.is_featured = clean_input.get("isFeatured")

    entity.source = clean_input.get("source", "")

    entity.save()

    entity.add_follow(user)

    return {
        "entity": entity
    }


def resolve_edit_news(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements

    user = info.context["request"].user

    clean_input = remove_none_from_dict(input)

    if not info.context["request"].user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        entity = News.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not entity.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    if 'tags' in clean_input:
        entity.tags = clean_input.get("tags")

    if 'accessId' in clean_input:
        entity.read_access = access_id_to_acl(entity, clean_input.get("accessId"))

    if 'writeAccessId' in clean_input:
        entity.write_access = access_id_to_acl(entity, clean_input.get("writeAccessId"))

    if 'title' in clean_input:
        entity.title = clean_input.get("title")
    if 'description' in clean_input:
        entity.description = clean_input.get("description")
    if 'richDescription' in clean_input:
        entity.rich_description = clean_input.get("richDescription")

    if 'featured' in clean_input:
        entity.featured_position_y = clean_input.get("featured").get("positionY", 0)
        entity.featured_video = clean_input.get("featured").get("video", None)
        if entity.featured_video:
            entity.featured_image = None
        elif clean_input.get("featured").get("image"):

            if entity.featured_image:
                imageFile = entity.featured_image
            else:
                imageFile = FileFolder()

            imageFile.owner = entity.owner
            imageFile.read_access = entity.read_access
            imageFile.write_access = entity.write_access
            imageFile.upload = clean_input.get("featured").get("image")
            imageFile.save()

            resize_featured.delay(tenant_schema(), imageFile.guid)

            entity.featured_image = imageFile

        entity.featured_position_y = clean_input.get("featured").get("positionY", 0)
    else:
        entity.featured_image = None
        entity.featured_position_y = 0
        entity.featured_video = None


    if user.has_role(USER_ROLES.ADMIN) or user.has_role(USER_ROLES.EDITOR):
        if 'isFeatured' in clean_input:
            entity.is_featured = clean_input.get("isFeatured")

    if 'source' in clean_input:
        entity.source = clean_input.get("source")

    entity.save()

    return {
        "entity": entity
    }
