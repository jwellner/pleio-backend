from core.models import GroupProfileFieldSetting, UserProfile, UserProfileField, Group, ProfileField


def resolve_member_profile_modal(_, info, groupGuid):
    # pylint: disable=unused-argument
    try:
        if info.context["request"].user.is_anonymous:
            raise ModalNotRequiredSignal()

        group = Group.objects.get(id=groupGuid)

        required_profile_fields = [setting.profile_field.id for setting in
                                   GroupProfileFieldSetting.objects.filter(group=group, is_required=True)]

        if len(required_profile_fields) == 0:
            raise ModalNotRequiredSignal()

        profile = UserProfile.objects.get(user=info.context["request"].user)
        existing_profile_fields = [field.profile_field.id for field in
                                   UserProfileField.objects.filter(user_profile=profile)]
        missing_profile_fields = [field_id for field_id in required_profile_fields if field_id not in existing_profile_fields]

        if len(missing_profile_fields) == 0:
            raise ModalNotRequiredSignal()

        return {
            "total": len(missing_profile_fields),
            "edges": ProfileField.objects.filter(id__in=missing_profile_fields),
            "intro": group.required_fields_message
        }

    except (ModalNotRequiredSignal, UserProfile.DoesNotExist):
        pass

    return {'total': 0}


class ModalNotRequiredSignal(Exception):
    pass
