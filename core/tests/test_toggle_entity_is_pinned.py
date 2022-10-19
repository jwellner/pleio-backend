from core.models import Group
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from blog.models import Blog
from mixer.backend.django import mixer


class ToggleEntityIsPinnedTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.user = mixer.blend(User)
        self.admin = mixer.blend(User, roles=['ADMIN'])
        self.group_admin = mixer.blend(User)
        self.group_user = mixer.blend(User)
        self.group = mixer.blend(Group, owner=self.group_admin)
        self.group.join(self.group_admin, 'admin')
        self.group.join(self.group_user, 'member')

        self.blog1 = mixer.blend(Blog, owner=self.user)
        self.blog2 = mixer.blend(Blog, owner=self.user, group=self.group)
        self.mutation = """
            mutation toggleEntityIsPinned($input: toggleEntityIsPinnedInput!) {
                toggleEntityIsPinned(input: $input) {
                    success
                }
            }
        """

    def tearDown(self):
        self.user.delete()
        self.admin.delete()
        self.group_admin.delete()
        self.group_user.delete()
        self.blog1.delete()
        self.blog2.delete()
        self.group.delete()
        super().tearDown()

    def test_toggle_entity_is_pinned_by_anonymous(self):
        variables = {
            "input": {
                "guid": self.blog1.guid
            }
        }

        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(self.mutation, variables)

    def test_toggle_entity_is_pinned_by_user_no_group(self):
        variables = {
            "input": {
                "guid": self.blog1.guid
            }
        }

        with self.assertGraphQlError("could_not_save"):
            self.graphql_client.force_login(self.user)
            self.graphql_client.post(self.mutation, variables)

    def test_toggle_is_pinned_by_admin_no_group(self):
        variables = {
            "input": {
                "guid": self.blog1.guid
            }
        }

        with self.assertGraphQlError("could_not_save"):
            self.graphql_client.force_login(self.admin)
            self.graphql_client.post(self.mutation, variables)

    def test_toggle_is_pinned_by_admin(self):
        variables = {
            "input": {
                "guid": self.blog2.guid
            }
        }

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, variables)

        data = result["data"]
        self.assertEqual(data["toggleEntityIsPinned"]["success"], True)

        self.blog2.refresh_from_db()
        self.assertEqual(self.blog2.is_pinned, True)

        result = self.graphql_client.post(self.mutation, variables)

        data = result["data"]
        self.assertEqual(data["toggleEntityIsPinned"]["success"], True)

        self.blog2.refresh_from_db()
        self.assertEqual(self.blog2.is_pinned, False)

    def test_toggle_is_pinned_by_group_admin(self):
        variables = {
            "input": {
                "guid": self.blog2.guid
            }
        }

        self.graphql_client.force_login(self.group_admin)
        result = self.graphql_client.post(self.mutation, variables)

        data = result["data"]
        self.assertEqual(data["toggleEntityIsPinned"]["success"], True)

        self.blog2.refresh_from_db()
        self.assertEqual(self.blog2.is_pinned, True)

        result = self.graphql_client.post(self.mutation, variables)

        data = result["data"]
        self.assertEqual(data["toggleEntityIsPinned"]["success"], True)
        self.blog2.refresh_from_db()
        self.assertEqual(self.blog2.is_pinned, False)

    def test_toggle_is_pinned_by_group_user(self):
        variables = {
            "input": {
                "guid": self.blog2.guid
            }
        }

        with self.assertGraphQlError("could_not_save"):
            self.graphql_client.force_login(self.group_user)
            self.graphql_client.post(self.mutation, variables)
