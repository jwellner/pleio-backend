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


class VoteOnPollTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
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

    def test_vote_on_poll(self):

        variables = self.data

        request = HttpRequest()
        request.user = self.authenticatedUser1

        result = graphql_sync(schema, {"query": self.mutation, "variables": variables }, context_value=request)

        data = result[1]["data"]

        self.assertEqual(data["voteOnPoll"]["entity"]["guid"], self.poll.guid)
        self.assertEqual(data["voteOnPoll"]["entity"]["hasVoted"], True)
        self.assertEqual(len(data["voteOnPoll"]["entity"]["choices"]), 3)
        self.assertEqual(data["voteOnPoll"]["entity"]["choices"][0]["text"], "answer1")
        self.assertEqual(data["voteOnPoll"]["entity"]["choices"][0]["votes"], 0)
        self.assertEqual(data["voteOnPoll"]["entity"]["choices"][1]["text"], "answer2")
        self.assertEqual(data["voteOnPoll"]["entity"]["choices"][1]["votes"], 1)

        request.user = self.authenticatedUser2

        result = graphql_sync(schema, {"query": self.mutation, "variables": variables }, context_value=request)

        data = result[1]["data"]

        self.assertEqual(data["voteOnPoll"]["entity"]["guid"], self.poll.guid)
        self.assertEqual(data["voteOnPoll"]["entity"]["hasVoted"], True)
        self.assertEqual(len(data["voteOnPoll"]["entity"]["choices"]), 3)
        self.assertEqual(data["voteOnPoll"]["entity"]["choices"][0]["text"], "answer1")
        self.assertEqual(data["voteOnPoll"]["entity"]["choices"][0]["votes"], 0)
        self.assertEqual(data["voteOnPoll"]["entity"]["choices"][1]["text"], "answer2")
        self.assertEqual(data["voteOnPoll"]["entity"]["choices"][1]["votes"], 2)

        request.user = self.authenticatedUser2

        result = graphql_sync(schema, {"query": self.mutation, "variables": variables }, context_value=request)

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "already_voted")
