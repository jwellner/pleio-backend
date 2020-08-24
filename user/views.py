import csv
from django.http import Http404, StreamingHttpResponse
from core.lib import get_exportable_user_fields
from core.models.group import GroupMembership
from core.models.user import UserProfileField, ProfileField
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
    return field_object.value_from_object(user)


def get_fields(user, user_fields, profile_field_guids):
    fields = []
    for user_field in user_fields:
        if user_field == 'guid':
            fields.append(str(user.id))
        elif user_field == 'name':
            fields.append(get_user_field(user, 'name'))
        elif user_field == 'email':
            fields.append(get_user_field(user, 'email'))
        elif user_field == 'created_at':
            fields.append(get_user_field(user, 'created_at'))
        elif user_field == 'updated_at':
            fields.append(get_user_field(user, 'updated_at'))
        elif user_field == 'last_online':
            fields.append(get_user_field(user, 'last_online'))
        elif user_field == 'banned':
            fields.append(get_user_field(user, 'is_active'))
        # ban reason not implemented yet
        elif user_field == 'ban_reason':
            fields.append("")
        elif user_field == 'group_memberships':
            group_memberships = list(GroupMembership.objects.filter(user=user, type__in=['owner', 'admin', 'member']).values_list("group__name", flat=True))
            fields.append(",".join(group_memberships))
        elif user_field == 'receive_newsletter':
            fields.append(get_user_field(user, 'receive_newsletter'))
        else:
            raise Http404("Error retreiving field of user")

    for guid in profile_field_guids:
        try:
            fields.append(UserProfileField.objects.get(user_profile=user.profile, profile_field__id=guid).value)
        except Exception:
            fields.append("")

    return fields


def export(request):
    # TODO: add check if setting for exporting is set
    # TODO: add tests
    user = request.user

    if not user.is_authenticated:
        raise Http404("Not logged in")

    if not user.is_admin:
        raise Http404("Not admin")

    user_fields = request.GET.getlist('user_fields[]')
    profile_field_guids = request.GET.getlist('profile_field_guids[]')

    if not user_fields and profile_field_guids:
        raise Http404("No fields passed")

    exportable_user_fields = [d['field'] for d in get_exportable_user_fields()]

    for user_field in user_fields:
        if user_field not in exportable_user_fields:
            raise Http404("User field " + user_field + " can not be exported")

    profile_field_names = []
    for guid in profile_field_guids:
        try:
            profile_field_names.append(ProfileField.objects.get(id=guid).name)
        except Exception:
            raise Http404("Profile field can not be exported")

    headers = user_fields + profile_field_names

    rows = [headers]
    for user in User.objects.all():
        fields = get_fields(user, user_fields, profile_field_guids)
        rows.append(fields)

    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer, delimiter=';', quotechar='"')
    writer.writerow(headers)
    response = StreamingHttpResponse((writer.writerow(row) for row in rows),
                                     content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename=exported_users.csv'
    return response
