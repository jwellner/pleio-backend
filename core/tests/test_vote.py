from blog.factories import BlogFactory
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class VoteTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.authenticatedUser = UserFactory()

        self.blog1 = BlogFactory(owner=self.authenticatedUser,
                                 title="Test1",
                                 rich_description="",
                                 is_recommended=True)

    def tearDown(self):
        self.blog1.delete()
        self.authenticatedUser.delete()
        super().tearDown()

    def test_bookmark(self):
        query = """
            mutation ($input: voteInput!) {
                vote(input: $input) {
                    object {
                        guid
                    }
                }
            }
        """

        variables = {
            "input": {
                "guid": self.blog1.guid,
                "score": 1
            }
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(query, variables)

        data = result["data"]
        self.assertEqual(data["vote"]["object"]["guid"], self.blog1.guid)
        self.assertEqual(self.blog1.vote_count(), 1)

        # Test "unvote"
        variables = {
            "input": {
                "guid": self.blog1.guid,
                "score": -1
            }
        }

        result = self.graphql_client.post(query, variables)

        data = result["data"]
        self.assertEqual(data["vote"]["object"]["guid"], self.blog1.guid)
        self.assertEqual(self.blog1.vote_count(), 0)

        # Test "down-vote"
        variables = {
            "input": {
                "guid": self.blog1.guid,
                "score": -1
            }
        }

        result = self.graphql_client.post(query, variables)

        data = result["data"]
        self.assertEqual(data["vote"]["object"]["guid"], self.blog1.guid)
        self.assertEqual(self.blog1.vote_count(), -1)
