from core.tests.helpers import PleioTenantTestCase
from user.models import User
from blog.models import Blog
from mixer.backend.django import mixer
from core.constances import ACCESS_TYPE


class FollowTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.authenticatedUser = mixer.blend(User)

        self.blog1 = Blog.objects.create(
            title="Test1",
            rich_description="",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            is_recommended=True
        )

    def tearDown(self):
        # self.blog1.get_follow(self.authenticatedUser).delete()
        self.blog1.delete()
        self.authenticatedUser.delete()
        super().tearDown()

    def test_bookmark(self):
        query = """
            mutation ($input: followInput!) {
                follow(input: $input) {
                    object {
                        guid
                    }
                }
            }
        """
        variables = {
            "input": {
                "guid": self.blog1.guid,
                "isFollowing": True
            }
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(query, variables)

        data = result["data"]

        self.assertEqual(data["follow"]["object"]["guid"], self.blog1.guid)
        self.assertTrue(self.blog1.is_following(self.authenticatedUser))

        # Test unfollow
        variables = {
            "input": {
                "guid": self.blog1.guid,
                "isFollowing": False
            }
        }

        result = self.graphql_client.post(query, variables)

        data = result["data"]
        self.assertEqual(data["follow"]["object"]["guid"], self.blog1.guid)
        self.assertFalse(self.blog1.is_following(self.authenticatedUser))
