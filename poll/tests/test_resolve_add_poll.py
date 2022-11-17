from core.tests.helpers import PleioTenantTestCase
from user.models import User
from mixer.backend.django import mixer


class AddPollTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.authenticatedUser = mixer.blend(User)
        self.mutation = """
            mutation AddPoll($input: addPollInput!) {
                addPoll(input: $input) {
                    entity {
                        guid
                        status
                        ...PollDetailFragment
                    }
                }
            }
            fragment PollDetailFragment on Poll {
                title
                url
                accessId
                timeCreated
                hasVoted
                canEdit
                choices {
                    guid
                    text
                    votes
                }
            }

        """
        self.data = {
            "input": {
                "accessId": 2,
                "choices": ["answer1", "answer2", "answer3"],
                "title": "test poll"
            }
        }

    def tearDown(self):
        self.authenticatedUser.delete()
        super().tearDown()

    def test_add_poll(self):
        variables = self.data

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, variables)

        data = result["data"]
        self.assertEqual(data["addPoll"]["entity"]["title"], variables["input"]["title"])
        self.assertEqual(data["addPoll"]["entity"]["accessId"], variables["input"]["accessId"])
        self.assertEqual(len(data["addPoll"]["entity"]["choices"]), 3)
        self.assertEqual(data["addPoll"]["entity"]["choices"][0]["text"], "answer1")

    def test_add_minimal_entity(self):
        variables = {
            'input': {
                'title': "Simple poll",
                'choices': ['One', 'More']
            }
        }
        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result["data"]["addPoll"]["entity"]
        self.assertTrue(entity['canEdit'])
