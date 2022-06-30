from backend2.schema import schema
from ariadne import graphql_sync
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from mixer.backend.django import mixer


class AddPollTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)

        self.data = {
            "input": {
                "accessId": 2,
                "choices": ["answer1", "answer2", "answer3"],
                "title": "test poll"
                }
            }

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

    def tearDown(self):
        self.authenticatedUser.delete()

    def test_add_poll(self):

        variables = self.data

        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, {"query": self.mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

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
