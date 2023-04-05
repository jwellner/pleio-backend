import csv

from django.http import Http404
from core.models.user import UserProfileField, ProfileField
from .serializers import *
from ..exception import ExportError


class ExportUsers:
    AVAILABLE_SERIALIZERS = [
        GuidSerializer,
        NameSerializer,
        EmailSerializer,
        CreateDateSerializer,
        UpdatedDateSerializer,
        LastOnlineDateSerializer,
        BannedSerializer,
        BanReasonSerialiser,
        GroupMembershipsSerializer,
        ReceiveNewsletterSerializer,
        CreateDateUnixSerializer,
        UpdatedAtUnixSerializer,
        LastOnlineUnixDateSerializer,
    ]

    def __init__(self, queryset, user_fields, profile_field_guids):
        self.queryset = queryset
        self.profile_field_guids = profile_field_guids
        self.serializers = {s.field: s for s in self.AVAILABLE_SERIALIZERS}
        self.user_fields = [*filter(lambda x: x in user_fields, [s.field for s in self.AVAILABLE_SERIALIZERS])]

    def get_native_fields(self, user):
        for user_field in self.user_fields:
            yield self.serializers[user_field].get_value(user)

    def get_profile_fields(self, user):
        for guid in self.profile_field_guids:
            try:
                yield UserProfileField.objects.get(user_profile=user.profile, profile_field__id=guid).value
            except Exception:
                yield ""

    def get_headers(self):
        profile_field_names = []
        for guid in self.profile_field_guids:
            try:
                profile_field_names.append(ProfileField.objects.get(id=guid).name)
            except Exception:
                raise ExportError("Profile field can not be exported")

        return self.user_fields + profile_field_names

    def get_data(self, user):
        return [*self.get_native_fields(user), *self.get_profile_fields(user)]

    def stream(self, buffer):
        writer = csv.writer(buffer, delimiter=';', quotechar='"')
        yield writer.writerow(self.get_headers())

        for user in self.queryset:
            yield writer.writerow(self.get_data(user))
