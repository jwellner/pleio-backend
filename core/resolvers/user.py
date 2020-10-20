from ariadne import ObjectType
from core import config
from core.constances import ACCESS_TYPE, USER_ROLES
from core.models import ProfileField, UserProfileField
from django.core.exceptions import ObjectDoesNotExist

user = ObjectType("User")

def is_user_or_admin(obj, info):
    if info.context["request"].user == obj or info.context["request"].user.has_role(USER_ROLES.ADMIN):
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
    profile_section_guids = []

    for section in config.PROFILE_SECTIONS:
        profile_section_guids.extend(section['profileFieldGuids'])

    for guid in profile_section_guids:
        field = ProfileField.objects.get(id=guid)
        field.value = ""
        field.read_access = []
        try:
            qs = UserProfileField.objects.visible(info.context["request"].user)
            field.value = qs.get(profile_field=field, user_profile=obj.profile).value
        except ObjectDoesNotExist:
            pass
        try:
            qs = UserProfileField.objects.visible(info.context["request"].user)
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

@user.field("roles")
def resolve_roles(obj, info):
    if not info.context["request"].user.has_role(USER_ROLES.ADMIN):
        return None

    return obj.roles

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

@user.field("fieldsInOverview")
def resolve_fields_in_overview(obj, info):
    # pylint: disable=unused-argument
    user_profile_fields = []

    # only get configured profile fields
    profile_section_guids = []

    for section in config.PROFILE_SECTIONS:
        profile_section_guids.extend(section['profileFieldGuids'])

    for field in ProfileField.objects.filter(id__in=profile_section_guids, is_in_overview=True):
        field.value = ""
        field.label = field.name
        try:
            qs = UserProfileField.objects.visible(info.context["request"].user)
            field.value = qs.get(profile_field=field, user_profile=obj.profile).value
        except ObjectDoesNotExist:
            pass

        user_profile_fields.append(field)
    return user_profile_fields
