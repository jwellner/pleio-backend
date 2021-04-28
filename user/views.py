import csv
from django.http import Http404, StreamingHttpResponse
from django.utils.dateformat import format as dateformat
from core.lib import get_exportable_user_fields, datetime_isoformat
from core.models.group import GroupMembership
from core.models.user import UserProfileField, ProfileField
from core.constances import USER_ROLES
from user.models import User


class Echo:
    """An object that implements just the write method of the file-like
    interface.
    """
    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value

def get_user_field(user, field):
    field_object = User._meta.get_field(field)
    value = field_object.value_from_object(user)
    return value

def get_fields(user, user_fields, profile_field_guids):
    # pylint: disable=too-many-branches
    fields = []
    for user_field in user_fields:
        if user_field == 'guid':
            fields.append(str(user.id))
        elif user_field == 'name':
            fields.append(get_user_field(user, 'name'))
        elif user_field == 'email':
            fields.append(get_user_field(user, 'email'))
        elif user_field == 'created_at':
            fields.append(datetime_isoformat(get_user_field(user, 'created_at')))
        elif user_field == 'created_at_unix':
            timestamp = dateformat(get_user_field(user, 'created_at'), 'U')
            fields.append(timestamp)
        elif user_field == 'updated_at':
            fields.append(datetime_isoformat(get_user_field(user, 'updated_at')))
        elif user_field == 'updated_at_unix':
            timestamp = dateformat(get_user_field(user, 'updated_at'), 'U')
            fields.append(timestamp)
        elif user_field == 'last_online':
            if user.profile.last_online:
                fields.append(datetime_isoformat(user.profile.last_online))
            else:
                fields.append("")
        elif user_field == 'last_online_unix':
            if user.profile.last_online:
                fields.append(dateformat(user.profile.last_online, 'U'))
            else:
                fields.append("")
        elif user_field == 'banned':
            banned = not get_user_field(user, 'is_active')
            fields.append(banned)
        elif user_field == 'ban_reason':
            fields.append(get_user_field(user, 'ban_reason'))
        elif user_field == 'group_memberships':
            group_memberships = list(GroupMembership.objects.filter(user=user, type__in=['owner', 'admin', 'member']).values_list("group__name", flat=True))
            fields.append(",".join(group_memberships))
        elif user_field == 'receive_newsletter':
            fields.append(user.profile.receive_newsletter)
        else:
            raise Http404("Error retreiving field of user")

    for guid in profile_field_guids:
        try:
            fields.append(UserProfileField.objects.get(user_profile=user.profile, profile_field__id=guid).value)
        except Exception:
            fields.append("")

    return fields

def get_headers(user_fields, profile_field_guids):
    profile_field_names = []
    for guid in profile_field_guids:
        try:
            profile_field_names.append(ProfileField.objects.get(id=guid).name)
        except Exception:
            raise Http404("Profile field can not be exported")

    return user_fields + profile_field_names

def get_data(user, user_fields, profile_field_guids):
    return get_fields(user, user_fields, profile_field_guids)

def iter_items(items, pseudo_buffer, user_fields, profile_field_guids):
    writer = csv.writer(pseudo_buffer, delimiter=';', quotechar='"')
    yield writer.writerow(get_headers(user_fields, profile_field_guids))

    for item in items:
        yield writer.writerow(get_data(item, user_fields, profile_field_guids))

def export(request):
    user = request.user

    if not user.is_authenticated:
        raise Http404("Not logged in")

    if not user.has_role(USER_ROLES.ADMIN):
        raise Http404("Not admin")

    user_fields = request.GET.getlist('user_fields[]')
    profile_field_guids = request.GET.getlist('profile_field_guids[]')

    if not user_fields and not profile_field_guids:
        raise Http404("No fields passed")

    exportable_user_fields = [d['field'] for d in get_exportable_user_fields()]

    for user_field in user_fields:
        if user_field not in exportable_user_fields:
            raise Http404("User field " + user_field + " can not be exported")

    response = StreamingHttpResponse(
        streaming_content=(iter_items(User.objects.all(), Echo(), user_fields, profile_field_guids)),
        content_type='text/csv',
    )

    response['Content-Disposition'] = 'attachment;filename=exported_users.csv'

    return response
