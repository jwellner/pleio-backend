from core.tests.helpers import PleioTenantTestCase
from user.models import User
from mixer.backend.django import mixer
from unittest import mock


class InviteToSiteTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.admin = mixer.blend(User, roles=['ADMIN'])

    def tearDown(self):
        super().tearDown()

    @mock.patch('core.resolvers.mutation_invite_to_site.generate_code', return_value='6df8cdad5582833eeab4')
    @mock.patch('core.resolvers.mutation_invite_to_site.schedule_invite_to_site_mail')
    def test_invite_to_site_by_admin(self, mocked_mail, mocked_generate_code):
        mutation = """
            mutation InviteItem($input: inviteToSiteInput!) {
                inviteToSite(input: $input) {
                    success
                }
            }
        """

        variables = {
            "input": {
                "emailAddresses": ['a@a.nl', 'b@b.nl', 'c@c.nl'],
                "message": "<p>testMessageContent</p>"
            }
        }

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertEqual(data["inviteToSite"]["success"], True)
        self.assertEqual(mocked_mail.call_count, 3)

    def test_invite_to_site_by_user(self):
        mutation = """
            mutation InviteItem($input: inviteToSiteInput!) {
                inviteToSite(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "emailAddresses": ['a@a.nl', 'b@b.nl', 'c@c.nl'],
                "message": "<p>testMessageContent</p>"
            }
        }

        with self.assertGraphQlError("user_not_site_admin"):
            self.graphql_client.force_login(self.user1)
            self.graphql_client.post(mutation, variables)

    def test_invite_to_site_by_anonymous(self):
        mutation = """
            mutation InviteItem($input: inviteToSiteInput!) {
                inviteToSite(input: $input) {
                    success
                }
            }
        """

        variables = {
            "input": {
                "emailAddresses": ['a@a.nl', 'b@b.nl', 'c@c.nl'],
                "message": "<p>testMessageContent</p>"
            }
        }

        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(mutation, variables)
