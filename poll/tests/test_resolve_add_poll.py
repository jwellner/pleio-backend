from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group
from user.models import User
from ..models import Poll
from core.constances import ACCESS_TYPE
from mixer.backend.django import mixer
from graphql import GraphQLError
from datetime import datetime


class AddPollTestCase(FastTenantTestCase):

    def setUp(self):
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

        result = graphql_sync(schema, {"query": self.mutation, "variables": variables }, context_value={ 'request': request })

        data = result[1]["data"]

        self.assertEqual(data["addPoll"]["entity"]["title"], variables["input"]["title"])
        self.assertEqual(data["addPoll"]["entity"]["accessId"], variables["input"]["accessId"])
        self.assertEqual(len(data["addPoll"]["entity"]["choices"]), 3)
        self.assertEqual(data["addPoll"]["entity"]["choices"][0]["text"], "answer1")
