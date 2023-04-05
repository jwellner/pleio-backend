from django.utils.dateformat import format as dateformat

from core.lib import datetime_isoformat
from core.models import GroupMembership
from user.models import User

__all__ = ("GuidSerializer",
           "NameSerializer",
           "EmailSerializer",
           "CreateDateSerializer",
           "UpdatedDateSerializer",
           "CreateDateUnixSerializer",
           "UpdatedAtUnixSerializer",
           "LastOnlineDateSerializer",
           "LastOnlineUnixDateSerializer",
           "BannedSerializer",
           "BanReasonSerialiser",
           "GroupMembershipsSerializer",
           "ReceiveNewsletterSerializer")


class SerializerBase:
    field = None
    label = ''

    @classmethod
    def get_value(cls, user):
        return cls.get_user_field(user, cls.field)

    @staticmethod
    def get_user_field(instance, field):
        field_object = User._meta.get_field(field)
        value = field_object.value_from_object(instance)
        return value


class GuidSerializer(SerializerBase):
    field = 'guid'
    label = 'guid'

    @classmethod
    def get_value(cls, user):
        return user.guid


class NameSerializer(SerializerBase):
    field = 'name'
    label = 'name'


class EmailSerializer(SerializerBase):
    field = 'email'
    label = 'email'


class IsoDateSerializerBase(SerializerBase):

    @classmethod
    def get_value(cls, user):
        return datetime_isoformat(super().get_value(user))


class CreateDateSerializer(IsoDateSerializerBase):
    field = 'created_at'
    label = 'created_at'


class UpdatedDateSerializer(IsoDateSerializerBase):
    field = 'updated_at'
    label = 'updated_at'


class LastOnlineDateSerializer(IsoDateSerializerBase):
    field = 'last_online'
    label = 'last_online'

    @classmethod
    def get_value(cls, user):
        if user.profile.last_online:
            return datetime_isoformat(user.profile.last_online)
        return ''


class LastOnlineUnixDateSerializer(IsoDateSerializerBase):
    field = 'last_online_unix'
    label = 'last_online (U)'

    @classmethod
    def get_value(cls, user):
        if user.profile.last_online:
            return dateformat(user.profile.last_online, 'U')
        return ''


class UnixDateSerializerBase(SerializerBase):
    src_field = None

    @classmethod
    def get_value(cls, user):
        return dateformat(cls.get_user_field(user, cls.src_field), 'U')


class CreateDateUnixSerializer(UnixDateSerializerBase):
    field = 'created_at_unix'
    src_field = 'created_at'
    label = 'created_at (U)'


class UpdatedAtUnixSerializer(UnixDateSerializerBase):
    field = 'updated_at_unix'
    src_field = 'updated_at'
    label = 'updated_at (U)'


class BannedSerializer(SerializerBase):
    field = 'banned'
    label = 'banned'

    @classmethod
    def get_value(cls, user):
        return not cls.get_user_field(user, 'is_active')


class BanReasonSerialiser(SerializerBase):
    field = 'ban_reason'
    label = 'ban_reason'


class GroupMembershipsSerializer(SerializerBase):
    field = 'group_memberships'
    label = 'group_memberships'

    @classmethod
    def get_value(cls, user):
        group_memberships = list(GroupMembership.objects.filter(user=user, type__in=['owner', 'admin', 'member']).values_list("group__name", flat=True))
        return ",".join(group_memberships)


class ReceiveNewsletterSerializer(SerializerBase):
    field = 'receive_newsletter'
    label = 'receive_newsletter'

    @classmethod
    def get_value(cls, user):
        return user.profile.receive_newsletter
