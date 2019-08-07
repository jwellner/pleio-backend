from ariadne import ObjectType
from django.utils.text import slugify
from core.constances import MEMBERSHIP
from core.lib import get_settings, get_access_ids

group = ObjectType("Group")

@group.field("widgets")
def resolve_group_widgets(obj, info):
    # pylint: disable=unused-argument
    return []

@group.field("richDescription")
def resolve_group_rich_description(obj, info):
    # pylint: disable=unused-argument
    return obj.rich_description

@group.field("description")
def resolve_group_description(obj, info):
    # pylint: disable=unused-argument
    return obj.description

@group.field("welcomeMessage")
def resolve_welcome_message(obj, info):
    # pylint: disable=unused-argument
    return obj.welcome_message

@group.field("url")
def resolve_group_url(obj, info):
    # pylint: disable=unused-argument
    return "/groups/view/{}/{}".format(obj.guid, slugify(obj.name))

@group.field("isClosed")
def resolve_group_is_closed(obj, info):
    # pylint: disable=unused-argument
    return obj.is_closed

@group.field("isMembershipOnRequest")
def resolve_group_is_membership_on_request(obj, info):
    # pylint: disable=unused-argument
    return obj.is_membership_on_request

@group.field("autoNotification")
def auto_notification(obj, info):
    # pylint: disable=unused-argument
    return obj.auto_notification

@group.field("featured")
def resolve_group_featured(obj, info):
    # pylint: disable=unused-argument
    return {
        'image': None,
        'video': None,
        'positionY': 0
    }
@group.field("isFeatured")
def resolve_group_is_featured(obj, info):
    # pylint: disable=unused-argument
    return obj.is_featured

@group.field("canEdit")
def resolve_group_can_edit(obj, info):
    # pylint: disable=unused-argument
    return obj.can_write(info.context.user)

@group.field("subgroups")
def resolve_group_subgroups(obj, info):
    # pylint: disable=unused-argument
    return {
        'total': 0,
        'edges': []
    }

@group.field("invited")
def resolve_group_intived(obj, info):
    # pylint: disable=unused-argument
    return {
        'total': 0,
        'edges': []
    }

@group.field("membershipRequests")
def resolve_group_membership_requests(obj, info):
    # pylint: disable=unused-argument
    return {
        'total': 0,
        'edges': []
    }

@group.field("members")
def resolve_group_members(group, info, q=None, offset=0, limit=5, inSubgroupId=None, notInSubgroupId=None):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments

    members = group.members.filter(type__in=['admin', 'owner', 'member'])[offset:offset+limit]

    return {
        'total': members.count(),
        'edges': members
    }

@group.field("membership")
def resolve_membership(group, info):
    # pylint: disable=unused-argument
    user = info.context.user

    if group.is_full_member(user):
        return MEMBERSHIP.joined
    
    if group.is_pending_member(user):
        return MEMBERSHIP.requested
    
    return MEMBERSHIP.not_joined

@group.field("accessIds")
def resolve_access_ids(group, info):
    # pylint: disable=unused-argument

    accessIds = get_access_ids(group)

    return accessIds

@group.field("defaultAccessId")
def resolve_default_access_id(group, info):
    # pylint: disable=unused-argument
    settings = get_settings()

    # TODO: implement

    return settings["site"]["defaultAccessId"]
