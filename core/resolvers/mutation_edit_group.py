from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.models import Group
from core.constances import NOT_LOGGED_IN, COULD_NOT_SAVE, COULD_NOT_FIND, USER_ROLES
from core.lib import remove_none_from_dict, ACCESS_TYPE, tenant_schema
from file.models import FileFolder
from file.tasks import resize_featured

def resolve_edit_group(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements

    user = info.context["request"].user

    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        group = Group.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not group.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    if 'name' in clean_input:
        group.name = clean_input.get("name")

    if 'icon' in clean_input:
        icon_file = FileFolder.objects.create(
            owner=group.owner,
            upload=clean_input.get("icon"),
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(user.id)]
        )

        group.icon = icon_file

    if 'featured' in clean_input:
        group.featured_position_y = clean_input.get("featured").get("positionY", 0)
        group.featured_video = clean_input.get("featured").get("video", None)
        group.featured_video_title = clean_input.get("featured").get("videoTitle", "")
        group.featured_alt = clean_input.get("featured").get("alt", "")
        if group.featured_video:
            group.featured_image = None
        elif clean_input.get("featured").get("image"):

            if group.featured_image:
                group.featured_image.delete()

            imageFile = FileFolder()
            imageFile.owner = group.owner
            imageFile.read_access = [ACCESS_TYPE.public]
            imageFile.write_access = [ACCESS_TYPE.user.format(user.id)]
            imageFile.upload = clean_input.get("featured").get("image")
            imageFile.save()

            resize_featured.delay(tenant_schema(), imageFile.guid)

            group.featured_image = imageFile
    else:
        group.featured_image = None
        group.featured_position_y = 0
        group.featured_video = None
        group.featured_video_title = ""
        group.featured_alt = ""

    if 'richDescription' in clean_input:
        group.rich_description = clean_input.get("richDescription")

    if 'introduction' in clean_input:
        group.introduction = clean_input.get("introduction")
    if 'isIntroductionPublic' in clean_input:
        group.is_introduction_public = clean_input.get("isIntroductionPublic")
    if 'welcomeMessage' in clean_input:
        group.welcome_message = clean_input.get("welcomeMessage")

    if 'isClosed' in clean_input:
        group.is_closed = clean_input.get("isClosed")
    if 'isMembershipOnRequest' in clean_input:
        group.is_membership_on_request = clean_input.get("isMembershipOnRequest")
    if 'autoNotification' in clean_input:
        group.auto_notification = clean_input.get("autoNotification")

    if user.has_role(USER_ROLES.ADMIN):
        if 'isFeatured' in clean_input:
            group.is_featured = clean_input.get("isFeatured")
        if 'isLeavingGroupDisabled' in clean_input:
            group.is_leaving_group_disabled = clean_input.get("isLeavingGroupDisabled")
        if 'isAutoMembershipEnabled' in clean_input:
            group.is_auto_membership_enabled = clean_input.get("isAutoMembershipEnabled")

    if 'plugins' in clean_input:
        group.plugins = clean_input.get("plugins")
    if 'tags' in clean_input:
        group.tags = clean_input.get("tags")

    group.save()

    return {
        "group": group
    }
