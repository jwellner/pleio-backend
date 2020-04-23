from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from django.utils import timezone
from core.models import Group
from user.models import User
from ..models import Poll
from mixer.backend.django import mixer
from core.constances import ACCESS_TYPE
from core.lib import get_acl, access_id_to_acl
from django.utils.text import slugify


class PollTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)

        self.pollPublic = Poll.objects.create(
            title="Test public poll",
            description="Description",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser
        )

        self.pollPrivate = Poll.objects.create(
            title="Test private poll",
            description="Description",
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser
        )

        self.query = """
            query PollsItem($guid: String!) {
                entity(guid: $guid) {
                    guid
                    status
                    ...PollDetailFragment
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
        self.pollPublic.delete()
        self.pollPrivate.delete()
        self.authenticatedUser.delete()

    def test_poll_anonymous(self):

        request = HttpRequest()
        request.user = self.anonymousUser

        variables = {
            "guid": self.pollPublic.guid
        }

        result = graphql_sync(schema, { "query": self.query , "variables": variables}, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"]["guid"], self.pollPublic.guid)
        self.assertEqual(data["entity"]["title"], self.pollPublic.title)
        self.assertEqual(data["entity"]["accessId"], 2)
        self.assertEqual(data["entity"]["timeCreated"], str(self.pollPublic.created_at))
        self.assertEqual(data["entity"]["url"], "/polls/view/{}/{}".format(self.pollPublic.guid, slugify(self.pollPublic.title)))

        variables = {
            "guid": self.pollPrivate.guid
        }

        result = graphql_sync(schema, { "query": self.query , "variables": variables}, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"], None)

    def test_poll_private(self):
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {
            "guid": self.pollPrivate.guid
        }

        result = graphql_sync(schema, { "query": self.query , "variables": variables}, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"]["guid"], self.pollPrivate.guid)
        self.assertEqual(data["entity"]["title"], self.pollPrivate.title)
        self.assertEqual(data["entity"]["accessId"], 0)
        self.assertEqual(data["entity"]["timeCreated"], str(self.pollPrivate.created_at))
        self.assertEqual(data["entity"]["canEdit"], True)
        self.assertEqual(data["entity"]["hasVoted"], False)
        self.assertEqual(data["entity"]["choices"], [])
