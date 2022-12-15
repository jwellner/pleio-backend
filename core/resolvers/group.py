from ariadne import ObjectType
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Case, When, IntegerField
from core.constances import MEMBERSHIP, USER_ROLES
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


group.set_field("richDescription", shared.resolve_entity_rich_description)


@group.field("description")
def resolve_group_description(obj, info):
    # pylint: disable=unused-argument
    return obj.description


@group.field("welcomeMessage")
def resolve_welcome_message(obj, info):
    # pylint: disable=unused-argument
    return obj.welcome_message


@group.field("requiredProfileFieldsMessage")
def resolve_required_fields_message(obj, info):
    # pylint: disable=unused-argument
    return obj.required_fields_message


@group.field("introduction")
def resolve_introduction(obj, info):
    # pylint: disable=unused-argument
    user = info.context["request"].user

    if obj.is_introduction_public:
        return obj.introduction

    if user.is_authenticated and (obj.is_full_member(user) or user.has_role(USER_ROLES.ADMIN)):
        return obj.introduction

    return ""


@group.field("isIntroductionPublic")
def resolve_is_introduction_public(obj, info):
    # pylint: disable=unused-argument
    return obj.is_introduction_public


@group.field("url")
def resolve_group_url(obj, info):
    # pylint: disable=unused-argument
    return obj.url


@group.field("isClosed")
def resolve_group_is_closed(obj, info):
    # pylint: disable=unused-argument
    return obj.is_closed


@group.field("isHidden")
def resolve_group_is_hidden(obj, info):
    # pylint: disable=unused-argument
    return obj.is_hidden


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
    result = obj.serialize_featured()

    if obj.featured_image:
        result['image'] = obj.featured_image.embed_url

    return result


@group.field("isFeatured")
def resolve_group_is_featured(obj, info):
    # pylint: disable=unused-argument
    return obj.is_featured


@group.field("isLeavingGroupDisabled")
def resolve_group_is_leaving_group_disabled(obj, info):
    # pylint: disable=unused-argument
    return obj.is_leaving_group_disabled


@group.field("isAutoMembershipEnabled")
def resolve_group_is_auto_membership_enabled(obj, info):
    # pylint: disable=unused-argument
    return obj.is_auto_membership_enabled


@group.field("canEdit")
def resolve_group_can_edit(obj, info):
    # pylint: disable=unused-argument
    return obj.can_write(info.context["request"].user)


@group.field("canChangeOwnership")
def resolve_group_can_change_ownership(obj, info):
    # pylint: disable=unused-argument
    user = info.context["request"].user
    if not user.is_authenticated:
        return False

    if user == obj.owner or user.has_role(USER_ROLES.ADMIN):
        return True

    return False


@group.field("notificationMode")
def resolve_group_notification_mode(obj, info):
    # pylint: disable=unused-argument
    user = info.context["request"].user

    if not user.is_authenticated:
        return None

    try:
        return obj.members.get(user=user).notification_mode
    except ObjectDoesNotExist:
        return None


@group.field("subgroups")
def resolve_group_subgroups(obj, info):
    # pylint: disable=unused-argument
    return obj.subgroups.all()


@group.field("invite")
def resolve_group_invite(obj, info, q=None, offset=0, limit=10):
    # pylint: disable=unused-argument
    # TODO: schema must be altered, this should not be type InvitedList
    request_user = info.context["request"].user

    if not obj.can_write(request_user):
        return {
            'total': 0,
            'edges': []
        }

    if q:
        users = User.objects.filter(name__icontains=q)[offset:offset + limit]
    else:
        users = User.objects.all()[offset:offset + limit]

    invites = []

    for user in users:
        if user == info.context["request"].user:
            continue
        if obj.is_member(user):
            continue
        invite = GroupInvitation(invited_user=user)
        invite.invited = False
        invites.append(invite)

    edges = invites[offset:offset + limit]

    return {
        'total': len(invites),
        'edges': edges
    }


@group.field("invited")
def resolve_group_invited(obj, info, q=None, offset=0, limit=10):
    # pylint: disable=unused-argument
    request_user = info.context["request"].user

    if not obj.can_write(request_user):
        return {
            'total': 0,
            'edges': []
        }

    invited = obj.invitations.filter(group=obj)

    edges = invited[offset:offset + limit]
    return {
        'total': invited.count(),
        'edges': edges
    }


@group.field("membershipRequests")
def resolve_group_membership_requests(obj, info):
    # pylint: disable=unused-argument
    request_user = info.context["request"].user

    if not obj.can_write(request_user):
        return {
            'total': 0,
            'edges': []
        }

    membership_requests = obj.members.filter(type='pending')
    users = []
    for m in membership_requests:
        users.append(m.user)
    return {
        'total': len(users),
        'edges': users
    }


@group.field("memberCount")
def resolve_group_member_count(group, info):
    # pylint: disable=unused-argument
    return group.members.filter(type__in=['admin', 'owner', 'member'],
                                user__is_superadmin=False,
                                user__is_active=True).count()


@group.field("members")
def resolve_group_members(group, info, q=None, offset=0, limit=5, inSubgroupId=None, notInSubgroupId=None):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments

    request_user = info.context["request"].user
    if not request_user.is_authenticated:
        return {
            'total': 0,
            'edges': [],
        }

    members = group.members.filter(type__in=['admin', 'owner', 'member'],
                                   user__is_superadmin=False,
                                   user__is_active=True)

    if inSubgroupId:
        subgroup_members = Subgroup.objects.get(id=inSubgroupId).members.all()
        members = members.filter(user__in=subgroup_members)

    if notInSubgroupId:
        subgroup_members = Subgroup.objects.get(id=notInSubgroupId).members.all()
        members = members.exclude(user__in=subgroup_members)

    if q:
        members = members.filter(user__name__icontains=q)

    members = members.annotate(order_type=Case(When(type='owner', then=0), When(type='admin', then=1), default=2,
                                               output_field=IntegerField())).order_by('order_type', 'user__name')

    edges = members[offset:offset + limit]

    return {
        'total': members.count(),
        'edges': edges
    }


@group.field("membership")
def resolve_membership(group, info):
    user = info.context["request"].user

    if group.is_full_member(user):
        return MEMBERSHIP.joined

    if group.is_pending_member(user):
        return MEMBERSHIP.requested

    return MEMBERSHIP.not_joined


@group.field('memberRole')
def resolve_memberrole(group, info):
    user = info.context['request'].user

    if user.is_authenticated:
        if group.owner == user:
            return 'owner'

        membership = group.members.filter(user=user).first()
        if membership:
            return membership.type

    return None


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


@group.field("icon")
def resolve_icon(group, info):
    # pylint: disable=unused-argument

    if group.icon:
        return group.icon.embed_url

    return None


@group.field("showMemberProfileFields")
def resolve_profile_fields_filter(group, info):
    # pylint: disable=unused-argument
    return [setting.profile_field for setting in group.profile_field_settings.filter(show_field=True)]


@group.field("requiredProfileFields")
def resolve_required_profile_fields_filter(group, info):
    # pylint: disable=unused-argument
    return [setting.profile_field for setting in group.profile_field_settings.filter(is_required=True)]


@group.field("isSubmitUpdatesEnabled")
def resolve_updates_enabled_field(obj, info):
    # pylint: disable=unused-argument
    return obj.is_submit_updates_enabled


@group.field("defaultTags")
def resolve_default_tags(obj, info):
    # pylint: disable=unused-argument
    return obj.content_presets['defaultTags']


@group.field("defaultTagCategories")
def resolve_default_tag_categories(obj, info):
    # pylint: disable=unused-argument
    return obj.content_presets['defaultTagCategories']


group.set_field("excerpt", shared.resolve_entity_excerpt)
group.set_field("tags", shared.resolve_entity_tags)
group.set_field("tagCategories", shared.resolve_entity_categories)
