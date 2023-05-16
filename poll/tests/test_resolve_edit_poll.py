from core.tests.helpers import PleioTenantTestCase
from user.models import User
from ..models import Poll, PollChoice
from core.constances import ACCESS_TYPE
from mixer.backend.django import mixer


class EditPollTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.authenticatedUser = mixer.blend(User)
        self.poll = mixer.blend(
            Poll,
            title="test poll",
            owner=self.authenticatedUser,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)]
        )
        mixer.blend(PollChoice, poll=self.poll)

        self.data = {
            "input": {
                "accessId": 1,
                "choices": ["answer1", "answer2", "answer3", "answer4"],
                "guid": self.poll.guid,
                "title": "test poll edited"
                }
            }

        self.mutation = """
            mutation EditPoll($input: editPollInput!) {
                editPoll(input: $input) {
                    entity {
                        guid
                        ... on Poll {
                            title
                            accessId
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
        super().tearDown()

    def test_edit_poll(self):
        variables = self.data

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, variables)

        data = result["data"]
        self.assertEqual(data["editPoll"]["entity"]["title"], variables["input"]["title"])
        self.assertEqual(data["editPoll"]["entity"]["accessId"], variables["input"]["accessId"])
        self.assertEqual(len(data["editPoll"]["entity"]["choices"]), 4)
        self.assertEqual(data["editPoll"]["entity"]["choices"][0]["text"], "answer1")
