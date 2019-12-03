from ariadne import ObjectType
from core.models import ProfileField, UserProfileField
from django.core.exceptions import ObjectDoesNotExist

user = ObjectType("User")


@user.field("url")
def resolve_url(obj, info):
    # pylint: disable=unused-argument
    return "/user/{}/profile".format(obj.guid)

@user.field("profile")
def resolve_profile(obj, info):
    # pylint: disable=unused-argument
    user_profile_fields = []
    for field in ProfileField.objects.all():
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
            pass
        user_profile_fields.append(field)
    return user_profile_fields

@user.field("stats")
def resolve_stats(obj, info):
    # pylint: disable=unused-argument
    return []

@user.field("groupNotifications")
def resolve_group_notifications(obj, info):
    # pylint: disable=unused-argument
    return []

@user.field("icon")
def resolve_icon(obj, info):
    # pylint: disable=unused-argument
    return obj.picture

@user.field("canEdit")
def resolve_can_edit(obj, info):
    return info.context.user == obj

@user.field("username")
def resolve_username(obj, info):
    # pylint: disable=unused-argument
    return obj.guid

@user.field("requestDelete")
def resolve_request_delete(obj, info):
    # pylint: disable=unused-argument
    return obj.is_delete_requested
