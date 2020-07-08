from ariadne import ObjectType
from core import config
from core.constances import ACCESS_TYPE
from core.models import ProfileField, UserProfileField
from django.core.exceptions import ObjectDoesNotExist

user = ObjectType("User")

def is_user_or_admin(obj, info):
    if info.context.user == obj or info.context.user.is_admin:
        return True
    return False

@user.field("url")
def resolve_url(obj, info):
    # pylint: disable=unused-argument
    return obj.url

@user.field("profile")
def resolve_profile(obj, info):
    # pylint: disable=unused-argument
    user_profile_fields = []

    # only get configured profile fields
    profile_setting_keys = [d['key'] for d in config.PROFILE if 'key' in d]

    for field in ProfileField.objects.filter(key__in=profile_setting_keys):
        field.value = ""
        field.read_access = []
        try:
            qs = UserProfileField.objects.visible(info.context.user)
            field.value = qs.get(profile_field=field, user_profile=obj.profile).value
        except ObjectDoesNotExist:
            pass
        try:
            qs = UserProfileField.objects.visible(info.context.user)
            field.read_access = qs.get(profile_field=field, user_profile=obj.profile).read_access
        except ObjectDoesNotExist:
            field.read_access = [ACCESS_TYPE.logged_in]
        user_profile_fields.append(field)
    return user_profile_fields

@user.field("stats")
def resolve_stats(obj, info):
    # pylint: disable=unused-argument
    return []

@user.field("groupNotifications")
def resolve_group_notifications(obj, info):
    # pylint: disable=unused-argument
    if is_user_or_admin(obj, info):
        groups = []
        for membership in obj.memberships.filter(type__in=['admin', 'owner', 'member']):
            groups.append({"guid": membership.group.guid, "name": membership.group.name, "getsNotifications": membership.enable_notification})

        return groups
    return []

@user.field("emailNotifications")
def resolve_email_notifications(obj, info):
    # pylint: disable=unused-argument
    if is_user_or_admin(obj, info):
        return obj.profile.receive_notification_email
    return None

@user.field("emailOverview")
def resolve_email_overview(obj, info):
    # pylint: disable=unused-argument
    if is_user_or_admin(obj, info):
        return obj.profile
    return None

@user.field("getsNewsletter")
def resolve_gets_newsletter(obj, info):
    # pylint: disable=unused-argument
    if is_user_or_admin(obj, info):
        return obj.profile.receive_newsletter
    return None

@user.field("icon")
def resolve_icon(obj, info):
    # pylint: disable=unused-argument
    return obj.picture

@user.field("canEdit")
def resolve_can_edit(obj, info):
    if is_user_or_admin(obj, info):
        return True
    return False

@user.field("isAdmin")
def resolve_is_admin(obj, info):
    if not info.context.user.is_admin:
        return None
    return obj.is_admin

@user.field("username")
def resolve_username(obj, info):
    # pylint: disable=unused-argument
    return obj.guid

@user.field("requestDelete")
def resolve_request_delete(obj, info):
    # pylint: disable=unused-argument
    if is_user_or_admin(obj, info):
        return obj.is_delete_requested
    return None
