from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group
from user.models import User
from ..models import Poll, PollChoice
from core.constances import ACCESS_TYPE
from mixer.backend.django import mixer
from graphql import GraphQLError
from datetime import datetime


class EditPollTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
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
        self.authenticatedUser.delete()

    def test_edit_poll(self):

        variables = self.data

        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, {"query": self.mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["editPoll"]["entity"]["title"], variables["input"]["title"])
        self.assertEqual(data["editPoll"]["entity"]["accessId"], variables["input"]["accessId"])
        self.assertEqual(len(data["editPoll"]["entity"]["choices"]), 4)
        self.assertEqual(data["editPoll"]["entity"]["choices"][0]["text"], "answer1")
