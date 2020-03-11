from ariadne import ObjectType
from core.constances import MEMBERSHIP
from core.lib import get_access_ids
from core.models import GroupInvitation, Subgroup
from user.models import User
from core import config
from core.resolvers import shared

group = ObjectType("Group")

@group.field("widgets")
def resolve_group_widgets(obj, info):
    # pylint: disable=unused-argument
    return obj.widgets.all()

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
    return obj.url

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
    return obj.subgroups.all()

@group.field("invite")
def resolve_group_invite(obj, info, q=None, offset=0, limit=10):
    # pylint: disable=unused-argument
    # TODO: schema must be altered, this should not be type InvitedList
    if q:
        users = User.objects.filter(name__icontains=q)[offset:offset+limit]
    else:
        users = User.objects.all()[offset:offset+limit]

    invites = []

    for user in users:
        if user == info.context.user:
            continue
        if obj.is_member(user):
            continue
        invite = GroupInvitation(invited_user=user)
        invite.invited = False
        invites.append(invite)

    edges = invites[offset:offset+limit]

    return {
        'total': len(invites),
        'edges': edges
    }

@group.field("invited")
def resolve_group_invited(obj, info, q=None, offset=0, limit=10):
    # pylint: disable=unused-argument
    invited = obj.invitations.filter(group=obj)

    edges = invited[offset:offset+limit]
    return {
        'total': invited.count(),
        'edges': edges
    }

@group.field("membershipRequests")
def resolve_group_membership_requests(obj, info):
    # pylint: disable=unused-argument
    membership_requests = obj.members.filter(type='pending')
    users = []
    for m in membership_requests:
        users.append(m.user)
    return {
        'total': len(users),
        'edges': users
    }

@group.field("members")
def resolve_group_members(group, info, q=None, offset=0, limit=5, inSubgroupId=None, notInSubgroupId=None):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments

    members = group.members.filter(type__in=['admin', 'owner', 'member'])

    if inSubgroupId:
        subgroup_members = Subgroup.objects.get(id=inSubgroupId).members.all()
        members = members.filter(user__in=subgroup_members)

    if notInSubgroupId:
        subgroup_members = Subgroup.objects.get(id=notInSubgroupId).members.all()
        members = members.exclude(user__in=subgroup_members)

    if q:
        members = members.filter(user__name__icontains=q)

    edges = members[offset:offset+limit]

    return {
        'total': members.count(),
        'edges': edges
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

    if group.is_closed:
        return 4

    return config.DEFAULT_ACCESS_ID


group.set_field("excerpt", shared.resolve_entity_excerpt)