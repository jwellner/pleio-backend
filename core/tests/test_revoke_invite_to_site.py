from core.tests.helpers import PleioTenantTestCase
from user.models import User
from mixer.backend.django import mixer


class RevokeInviteToSiteTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.admin = mixer.blend(User, roles=['ADMIN'])

        self.mutation = """
            mutation InviteItem($input: revokeInviteToSiteInput!) {
                revokeInviteToSite(input: $input) {
                    success
                }
            }
        """
        self.variables = {
            "input": {
                "emailAddresses": ['a@a.nl', 'b@b.nl', 'c@c.nl']
            }
        }


    def tearDown(self):
        self.admin.delete()
        self.user2.delete()
        self.user1.delete()
        super().tearDown()

    def test_revoke_invite_to_site_by_admin(self):
        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, self.variables)

        data = result["data"]
        self.assertEqual(data["revokeInviteToSite"]["success"], True)

    def test_revoke_invite_to_site_by_user(self):
        with self.assertGraphQlError("user_not_site_admin"):
            self.graphql_client.force_login(self.user1)
            self.graphql_client.post(self.mutation, self.variables)

    def test_revoke_invite_to_site_by_anonymous(self):
        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(self.mutation, self.variables)
