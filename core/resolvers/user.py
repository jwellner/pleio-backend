from ariadne import ObjectType
from core import config
from core.constances import ACCESS_TYPE, USER_ROLES, COULD_NOT_FIND
from core.lib import get_language_options
from core.models import ProfileField, UserProfileField, Group, GroupProfileFieldSetting, UserProfile
from django.core.exceptions import ObjectDoesNotExist
from graphql import GraphQLError

from core.resolvers import shared

user = ObjectType("User")


def is_user_or_admin(obj, info):
    request_user = info.context["request"].user

    if request_user.is_authenticated and (request_user == obj or request_user.has_role(USER_ROLES.ADMIN)):
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
        user_profile_fields.append(obj.profile.profile_field_value(field, info.context["request"].user))

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
            groups.append(
                {
                    "guid": membership.group.guid,
                    "name": membership.group.name,
                    "notificationMode": membership.notification_mode
                }
            )
        return groups
    return []


@user.field("emailNotifications")
def resolve_email_notifications(obj, info):
    # pylint: disable=unused-argument
    if is_user_or_admin(obj, info):
        return obj.profile.receive_notification_email
    return None


@user.field("emailNotificationsFrequency")
def resolve_email_notifications_frequency(obj, info):
    # pylint: disable=unused-argument
    if is_user_or_admin(obj, info):
        return obj.profile.notification_email_interval_hours
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
    return obj.icon


@user.field("canEdit")
def resolve_can_edit(obj, info):
    if is_user_or_admin(obj, info):
        return True
    return False


@user.field("roles")
def resolve_roles(obj, info):
    if is_user_or_admin(obj, info):
        return obj.roles
    return None


@user.field("isSuperadmin")
def resolve_is_superadmin(obj, info):
    if is_user_or_admin(obj, info):
        return obj.is_superadmin
    return None


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


@user.field("language")
def resolve_language(obj, info):
    # pylint: disable=unused-argument
    if is_user_or_admin(obj, info):
        return obj.get_language()
    return None


@user.field("languageOptions")
def resolve_language_options(obj, info):
    # pylint: disable=unused-argument
    active_languages = config.EXTRA_LANGUAGES
    active_languages.append(config.LANGUAGE)
    return [i for i in get_language_options() if i['value'] in active_languages]


@user.field("fieldsInOverview")
def resolve_fields_in_overview(obj, info, groupGuid=None):
    # pylint: disable=unused-argument

    if groupGuid:
        try:
            group = Group.objects.get(id=groupGuid)
        except Group.DoesNotExist:
            raise GraphQLError(COULD_NOT_FIND)
    else:
        group = None

    user_profile_fields = []

    # only get configured profile fields
    profile_section_guids = []

    for section in config.PROFILE_SECTIONS:
        profile_section_guids.extend(section['profileFieldGuids'])

    if group:
        for setting in group.profile_field_settings.filter(show_field=True):
            if setting.profile_field.guid in profile_section_guids:
                field = {
                    'key': setting.profile_field.key,
                    'label': setting.profile_field.name,
                    'value': ''
                }
                try:
                    qs = UserProfileField.objects.visible(info.context["request"].user)
                    field['value'] = qs.get(profile_field=setting.profile_field, user_profile=obj.profile).value
                except ObjectDoesNotExist:
                    pass

                user_profile_fields.append(field)
    else:
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


@user.field("email")
def resolve_email(obj, info):
    # pylint: disable=unused-argument
    if is_user_or_admin(obj, info):
        return obj.email
    return None


@user.field("lastOnline")
def resolve_last_online(obj, info):
    # pylint: disable=unused-argument
    if is_user_or_admin(obj, info):
        return obj.profile.last_online
    return None


@user.field("vcard")
def resolve_vcard(obj, info):
    profile_fields = ProfileField.objects.filter(is_on_vcard=True)
    return filter(lambda x: x.value != '',
                  [obj.profile.profile_field_value(field, info.context["request"].user) for field in profile_fields])


@user.field("memberSince")
def resolve_created_at(obj, info):
    # pylint: disable=unused-argument
    return obj.created_at


@user.field('missingProfileFields')
def resolve_missing_profile_fields(obj, info, groupGuid):
    if getattr(info.context['request'].user, 'is_superadmin', False):
        return []

    # pylint: disable=unused-argument
    class ModalNotRequiredSignal(Exception):
        pass

    try:
        group = Group.objects.get(id=groupGuid)

        required_profile_fields = [setting.profile_field.id for setting in
                                   GroupProfileFieldSetting.objects.filter(group=group, is_required=True)]

        if not required_profile_fields:
            raise ModalNotRequiredSignal()

        profile = UserProfile.objects.get(user=obj)
        existing_profile_fields = [field.profile_field.id for field in
                                   UserProfileField.objects.filter(user_profile=profile) if not field.is_empty]
        missing_profile_fields = [field_id for field_id in required_profile_fields if
                                  field_id not in existing_profile_fields]

        missing_profile_fields_result = []
        for field in ProfileField.objects.filter(id__in=missing_profile_fields):
            field.read_access = []
            try:
                user_profile_field = UserProfileField.objects.visible(info.context["request"].user).get(
                    profile_field=field,
                    user_profile=obj.profile)
                field.read_access = user_profile_field.read_access
            except ObjectDoesNotExist:
                field.read_access = [ACCESS_TYPE.logged_in]
            missing_profile_fields_result.append(field)

        if len(missing_profile_fields) == 0:
            raise ModalNotRequiredSignal()

        return missing_profile_fields_result

    except (ModalNotRequiredSignal, UserProfile.DoesNotExist):
        pass

    return []


@user.field("profileSetManager")
def resolve_user_profile_set_manager(obj, info):
    # pylint: disable=unused-argument
    return obj.profile_sets.all()


user.set_field('canDelete', shared.has_full_admin_abilities_on_user)
user.set_field('canBan', shared.has_full_admin_abilities_on_user)
