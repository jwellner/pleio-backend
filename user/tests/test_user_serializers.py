from django.utils.timezone import now, datetime, timedelta, make_aware, utc

from core.factories import GroupFactory
from core.tests.helpers import PleioTenantTestCase
from user.exporting.serializers import *
from user.factories import UserFactory


class TestUserSerializersTestCase(PleioTenantTestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.entities = []

    def tearDown(self):
        for entity in self.entities:
            entity.delete()
        self.user.delete()
        super().tearDown()

    def create_entity(self, factory, **kwargs):
        entity = factory(**kwargs)
        self.entities.append(entity)
        return entity

    def datetime_from_unix(self, maybe_unix):
        aware_result = make_aware(datetime.fromtimestamp(int(maybe_unix)))
        return aware_result.astimezone(utc)

    def datetime_no_microsec(self, maybe_microsec: datetime):
        return maybe_microsec - timedelta(microseconds=maybe_microsec.microsecond)

    def test_guid_serializer(self):
        self.assertEqual(GuidSerializer.get_value(self.user), self.user.guid)

    def test_name_serializer(self):
        self.assertEqual(NameSerializer.get_value(self.user), self.user.name)

    def test_email_serializer(self):
        self.assertEqual(EmailSerializer.get_value(self.user), self.user.email)

    def test_create_date_serializer(self):
        result = CreateDateSerializer.get_value(self.user)
        expected = self.datetime_no_microsec(self.user.created_at)
        self.assertEqual(datetime.fromisoformat(result), expected)

    def test_updated_date_serializer(self):
        self.user.updated_at = now() - timedelta(11111)
        self.user.save()

        result = UpdatedDateSerializer.get_value(self.user)
        expected = self.datetime_no_microsec(self.user.updated_at)
        self.assertEqual(datetime.fromisoformat(result), expected)

    def test_last_online_date_serializer(self):
        self.user.profile.last_online = now() - timedelta(hours=2222)
        self.user.profile.save()

        result = LastOnlineDateSerializer.get_value(self.user)
        expected = self.datetime_no_microsec(self.user.profile.last_online)
        self.assertEqual(datetime.fromisoformat(result), expected)

    def test_not_ever_last_online_date_serializer(self):
        self.user.profile.last_online = None
        self.user.profile.save()

        self.assertEqual(LastOnlineDateSerializer.get_value(self.user), "")

    def test_banned_serializer(self):
        self.user.is_active = False
        self.user.save()
        self.assertTrue(BannedSerializer.get_value(self.user))

    def test_not_banned_serializer(self):
        self.user.is_active = True
        self.user.save()
        self.assertFalse(BannedSerializer.get_value(self.user))

    def test_ban_reason_serializer(self):
        self.user.ban_reason = "Foo"
        self.user.save()
        self.assertEqual(BanReasonSerialiser.get_value(self.user), "Foo")

    def test_group_membership_serializer(self):
        from core.models import Group
        other_owner = self.create_entity(
            UserFactory,
            name="Alpha")
        self.create_entity(
            GroupFactory, owner=self.user,
            name="Bravo")
        group2: Group = self.create_entity(
            GroupFactory, owner=other_owner,
            name="Charlie")
        group2.join(self.user)

        self.assertEqual(GroupMembershipsSerializer.get_value(self.user), "Bravo,Charlie")

    def test_newsletter_serializer(self):
        self.user.profile.receive_newsletter = True
        self.user.profile.save()

        self.assertTrue(ReceiveNewsletterSerializer.get_value(self.user))

    def test_no_newsletter_serializer(self):
        self.user.profile.receive_newsletter = False
        self.user.profile.save()

        self.assertFalse(ReceiveNewsletterSerializer.get_value(self.user))

    def test_created_unix_serializer(self):
        result = CreateDateUnixSerializer.get_value(self.user)
        expected = self.datetime_no_microsec(self.user.created_at)
        self.assertEqual(self.datetime_from_unix(result), expected)

    def test_updated_unix_serializer(self):
        self.user.updated_at = now() - timedelta(seconds=665544)
        self.user.save()

        result = UpdatedAtUnixSerializer.get_value(self.user)
        expected = self.datetime_no_microsec(self.user.updated_at)
        self.assertEqual(self.datetime_from_unix(result), expected)

    def test_last_online_unix_serializer(self):
        self.user.profile.last_online = now() - timedelta(minutes=5555)
        self.user.profile.save()

        result = LastOnlineUnixDateSerializer.get_value(self.user)
        expected = self.datetime_no_microsec(self.user.profile.last_online)
        self.assertEqual(self.datetime_from_unix(result), expected)

    def test_not_ever_last_online_unix_serializer(self):
        self.user.profile.last_online = None
        self.user.profile.save()

        self.assertEqual(LastOnlineUnixDateSerializer.get_value(self.user), "")
