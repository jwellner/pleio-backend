from core.tests.helpers import PleioTenantTestCase
from user.models import User
from ..models import Poll, PollChoice
from core.constances import ACCESS_TYPE
from mixer.backend.django import mixer


class VoteOnPollTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.authenticatedUser1 = mixer.blend(User)
        self.authenticatedUser2 = mixer.blend(User)
        self.poll = mixer.blend(
            Poll,
            title="test poll",
            owner=self.authenticatedUser1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser1.id)]
        )
        self.poll_choice_1 = PollChoice.objects.create(poll=self.poll, text="answer1")
        self.poll_choice_2 = PollChoice.objects.create(poll=self.poll, text="answer2")
        self.poll_choice_3 = PollChoice.objects.create(poll=self.poll, text="answer3")

        self.data = {
            "input": {
                "guid": self.poll.guid,
                "response": self.poll_choice_2.text
            }
        }

        self.mutation = """
            mutation Poll($input: voteOnPollInput!) {
                voteOnPoll(input: $input) {
                    entity {
                        guid
                        ... on Poll {
                            hasVoted
                            choices {
                                guid
                                text
                                votes
                            }
                        }
                    }
                }
            }
        """

    def tearDown(self):
        self.poll_choice_1.delete()
        self.poll_choice_2.delete()
        self.poll_choice_3.delete()
        self.poll.delete()
        self.authenticatedUser1.delete()
        self.authenticatedUser2.delete()
        super().tearDown()

    def test_vote_on_poll(self):
        variables = self.data

        self.graphql_client.force_login(self.authenticatedUser1)
        result = self.graphql_client.post(self.mutation, variables)

        data = result["data"]
        self.assertEqual(data["voteOnPoll"]["entity"]["guid"], self.poll.guid)
        self.assertEqual(data["voteOnPoll"]["entity"]["hasVoted"], True)
        self.assertEqual(len(data["voteOnPoll"]["entity"]["choices"]), 3)
        self.assertEqual(data["voteOnPoll"]["entity"]["choices"][0]["text"], "answer1")
        self.assertEqual(data["voteOnPoll"]["entity"]["choices"][0]["votes"], 0)
        self.assertEqual(data["voteOnPoll"]["entity"]["choices"][1]["text"], "answer2")
        self.assertEqual(data["voteOnPoll"]["entity"]["choices"][1]["votes"], 1)

        self.graphql_client.force_login(self.authenticatedUser2)
        result = self.graphql_client.post(self.mutation, variables)

        data = result["data"]
        self.assertEqual(data["voteOnPoll"]["entity"]["guid"], self.poll.guid)
        self.assertEqual(data["voteOnPoll"]["entity"]["hasVoted"], True)
        self.assertEqual(len(data["voteOnPoll"]["entity"]["choices"]), 3)
        self.assertEqual(data["voteOnPoll"]["entity"]["choices"][0]["text"], "answer1")
        self.assertEqual(data["voteOnPoll"]["entity"]["choices"][0]["votes"], 0)
        self.assertEqual(data["voteOnPoll"]["entity"]["choices"][1]["text"], "answer2")
        self.assertEqual(data["voteOnPoll"]["entity"]["choices"][1]["votes"], 2)

        with self.assertGraphQlError("already_voted"):
            self.graphql_client.post(self.mutation, variables)
