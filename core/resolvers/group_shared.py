from graphql import GraphQLError
from django.core.exceptions import ValidationError

from core.exceptions import AttachmentVirusScanError
from core.models import ProfileField, GroupProfileFieldSetting
from core.constances import INVALID_PROFILE_FIELD_GUID, FILE_NOT_CLEAN
from core.lib import ACCESS_TYPE
from core.widget_resolver import WidgetSerializer
from file.models import FileFolder


def update_name(group, clean_input):
    if 'name' in clean_input:
        group.name = clean_input.get("name")


def update_icon(group, clean_input, image_owner):
    if 'icon' in clean_input:
        icon_file = None
        if clean_input['icon']:
            icon_file = FileFolder.objects.create(
                owner=group.owner,
                upload=clean_input.get("icon"),
                read_access=[ACCESS_TYPE.public],
                write_access=[ACCESS_TYPE.user.format(image_owner.id)]
            )
        group.icon = icon_file


def update_is_leaving_group_disabled(group, clean_input):
    if 'isLeavingGroupDisabled' in clean_input:
        group.is_leaving_group_disabled = clean_input.get("isLeavingGroupDisabled")


def update_is_auto_membership_enabled(group, clean_input):
    if "isAutoMembershipEnabled" in clean_input:
        if not group.is_auto_membership_enabled and clean_input["isAutoMembershipEnabled"]:
            from user.models import User
            for u in User.objects.filter(is_active=True):
                if not group.is_full_member(u):
                    group.join(u, 'member')

        group.is_auto_membership_enabled = clean_input["isAutoMembershipEnabled"]


def update_is_hidden(group, clean_input):
    if 'isHidden' in clean_input:
        group.is_hidden = clean_input.get("isHidden")


def update_required_profile_fields(group, clean_input):
    if 'requiredProfileFieldGuids' in clean_input:
        for profile_field_id in clean_input.get("requiredProfileFieldGuids"):
            try:
                profile_field = ProfileField.objects.get(id=profile_field_id)
                setting, created = GroupProfileFieldSetting.objects.get_or_create(
                    profile_field=profile_field,
                    group=group
                )
                setting.is_required = True
                setting.save()
            except ProfileField.DoesNotExist:
                raise GraphQLError(INVALID_PROFILE_FIELD_GUID)
            except ValidationError as e:
                raise GraphQLError(', '.join(e.messages))
        # disable other
        group.profile_field_settings.exclude(
            profile_field__id__in=clean_input.get("requiredProfileFieldGuids")).update(is_required=False)


def update_show_member_profile_fields(group, clean_input):
    if 'showMemberProfileFieldGuids' in clean_input:
        for profile_field_id in clean_input.get("showMemberProfileFieldGuids"):
            try:
                profile_field = ProfileField.objects.get(id=profile_field_id)
                setting, created = GroupProfileFieldSetting.objects.get_or_create(
                    profile_field=profile_field,
                    group=group
                )
                setting.show_field = True
                setting.save()
            except ProfileField.DoesNotExist:
                raise GraphQLError(INVALID_PROFILE_FIELD_GUID)
            except ValidationError as e:
                raise GraphQLError(', '.join(e.messages))
        # disable other
        group.profile_field_settings.exclude(
            profile_field__id__in=clean_input.get("showMemberProfileFieldGuids")).update(show_field=False)


def update_plugins(group, clean_input):
    if 'plugins' in clean_input:
        group.plugins = clean_input.get("plugins")


def update_is_submit_updates_enabled(group, clean_input):
    if "isSubmitUpdatesEnabled" in clean_input:
        group.is_submit_updates_enabled = clean_input.get("isSubmitUpdatesEnabled")


def update_auto_notification(group, clean_input):
    if 'autoNotification' in clean_input:
        group.auto_notification = clean_input.get("autoNotification")


def update_is_membership_on_request(group, clean_input):
    if 'isMembershipOnRequest' in clean_input:
        group.is_membership_on_request = clean_input.get("isMembershipOnRequest")


def update_is_closed(group, clean_input):
    if 'isClosed' in clean_input:
        group.is_closed = clean_input.get("isClosed")


def update_is_introduction_public(group, clean_input):
    if 'isIntroductionPublic' in clean_input:
        group.is_introduction_public = clean_input.get("isIntroductionPublic")


def update_welcome_message(group, clean_input):
    if 'welcomeMessage' in clean_input:
        group.welcome_message = clean_input.get("welcomeMessage")


def update_required_profile_fields_message(group, clean_input):
    if 'requiredProfileFieldsMessage' in clean_input:
        group.required_fields_message = clean_input.get("requiredProfileFieldsMessage", "")


def update_widgets(group, clean_input):
    try:
        if 'widgets' in clean_input:
            group.widget_repository = [WidgetSerializer(w).serialize() for w in clean_input['widgets'] or []]
    except AttachmentVirusScanError as e:
        raise GraphQLError(FILE_NOT_CLEAN.format(str(e)))
