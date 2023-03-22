from django.contrib.auth.models import AnonymousUser

from core.factories import GroupFactory
from core.tests.helpers import PleioTenantTestCase
from event.factories import EventFactory
from user.factories import UserFactory, AdminFactory
from event.models import EventAttendee
from unittest import mock


class AttendEventWithoutAccountTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.override_config(EVENT_ADD_EMAIL_ATTENDEE='')

        self.authenticatedUser = UserFactory()
        self.owner = UserFactory()
        self.event = EventFactory(owner=self.owner)
        self.event.max_attendees = 1
        self.event.save()

        self.mutation = """
            mutation RequestAttendance($input: attendEventWithoutAccountInput!) {
                attendEvent: attendEventWithoutAccount(input: $input) {
                    entity {
                        guid
                        ... on Event {
                            title
                            __typename
                        }
                        __typename
                    }
                    __typename
                }
            }
        """
        self.variables = {
            "input": {
                "guid": self.event.guid,
                "name": "Pete",
                "email": "pete@tenant.fast-test.com"
            }
        }
        mock.patch('event.resolvers.mutation_attend_event.generate_code', return_value='6df8cdad5582833eeab4')

    def tearDown(self):
        self.event.delete()
        self.authenticatedUser.delete()
        super().tearDown()

    def test_create_attend_event_without_account_request(self):
        result = self.graphql_client.post(self.mutation, self.variables)

        data = result["data"]
        self.assertEqual(data["attendEvent"]["entity"]["guid"], self.event.guid)

    def test_attend_event_without_account_resend(self):
        self.graphql_client.post(self.mutation, self.variables)

        self.variables['input']['resend'] = True
        result = self.graphql_client.post(self.mutation, self.variables)

        data = result["data"]
        self.assertEqual(data["attendEvent"]["entity"]["guid"], self.event.guid)

    def test_attend_event_without_account_attend_twice(self):
        # given
        self.graphql_client.post(self.mutation, self.variables)

        # when, then
        with self.assertGraphQlError("email_already_used"):
            self.graphql_client.post(self.mutation, self.variables)

    def test_attend_event_is_full_without_account(self):
        EventAttendee.objects.create(
            event=self.event,
            state='accept',
            user=self.authenticatedUser,
            email=self.authenticatedUser.email
        )

        result = self.graphql_client.post(self.mutation, self.variables)

        data = result["data"]
        self.assertEqual(data["attendEvent"]["entity"]["guid"], self.event.guid)

    def test_attend_event_without_account_no_name(self):
        # Given
        self.variables['input']['name'] = ""

        # When, then
        with self.assertGraphQlError("invalid_name"):
            self.graphql_client.post(self.mutation, self.variables)

    def test_attend_as_super_admin_visitor(self):
        self.graphql_client.force_login(UserFactory(is_superadmin=True))
        self.graphql_client.post(self.mutation, self.variables)

        attendee = EventAttendee.objects.filter(email=self.variables['input']['email']).first()
        self.assertIsNotNone(attendee)
        self.assertEqual(attendee.state, 'accept')

    def test_attend_as_event_owner_visitor(self):
        with self.assertGraphQlError('not_authorized'):
            self.graphql_client.force_login(self.owner)
            self.graphql_client.post(self.mutation, self.variables)


class AttendEventByEmailTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.override_config(EVENT_ADD_EMAIL_ATTENDEE='')

        self.group_owner = UserFactory()
        self.group = GroupFactory(owner=self.group_owner)

        self.owner = UserFactory()
        self.group.join(self.owner)

        self.event = EventFactory(owner=self.owner,
                                  group=self.group)

        self.query = """
        query GetGroup ($guid: String) {
            entity(guid: $guid) {
                ... on Event {
                    canAttendWithEmail
                }
            }
        }
        """
        self.query_variables = {
            'guid': self.event.guid,
        }

        self.mutation = """
        mutation AttendWithEmailAddress($input: attendEventWithoutAccountInput!) {
            mutation: attendEventWithoutAccount(input: $input) {
                entity {
                    guid
                }
            }
        }
        """
        self.mutation_variables = {
            'input': {
                'guid': self.event.guid,
                'email': 'demo@example.com',
                'name': 'Demo User',
                'resend': False,
            }
        }

    def assertExpectation(self, user, description, expect_access):
        self.graphql_client.force_login(user)

        result = self.graphql_client.post(self.query, self.query_variables)
        msg = "Expected %s to be %s" % (description, 'rejected' if not expect_access else 'allowed')
        self.assertEqual(result['data']['entity']['canAttendWithEmail'], expect_access, msg)

        if expect_access:
            result = self.graphql_client.post(self.mutation, self.mutation_variables)
            self.assertEqual(result['data']['mutation']['entity']['guid'], self.event.guid)
        else:
            with self.assertGraphQlError():
                self.graphql_client.post(self.mutation, self.mutation_variables)

    def test_as_super_admin(self):
        self.assertExpectation(user=UserFactory(is_superadmin=True),
                               description="Superadmin",
                               expect_access=True)

    def test_as_anonymous_visitor(self):
        self.assertExpectation(user=AnonymousUser(),
                               description="Anonymous visitor",
                               expect_access=True)

    def test_as_authenticated_visitor(self):
        self.assertExpectation(user=UserFactory(),
                               description="Authenticated visitor",
                               expect_access=False)

    expect_admin = False

    def test_as_admin(self):
        self.assertExpectation(user=AdminFactory(),
                               description="Site admin",
                               expect_access=self.expect_admin)

    expect_group_admin = False

    def test_as_groupadmin(self):
        self.assertExpectation(user=self.group_owner,
                               description="Group admin",
                               expect_access=self.expect_group_admin)

    expect_owner = False

    def test_as_owner(self):
        self.assertExpectation(user=self.owner,
                               description="Event owner",
                               expect_access=self.expect_owner)


class AttendEventByEmailAllowAdminSettingTestCase(AttendEventByEmailTestCase):

    def setUp(self):
        super().setUp()
        self.override_config(EVENT_ADD_EMAIL_ATTENDEE='admin')

    expect_admin = True


class AttendEventByEmailAllowOwnerSettingTestCase(AttendEventByEmailTestCase):

    def setUp(self):
        super().setUp()
        self.override_config(EVENT_ADD_EMAIL_ATTENDEE='owner')

    expect_admin = True
    expect_group_admin = True
    expect_owner = True
