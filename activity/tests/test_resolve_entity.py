from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from django.utils import timezone
from core.models import User, Group
from ..models import StatusUpdate
from mixer.backend.django import mixer
from core.constances import ACCESS_TYPE
from core.lib import get_acl, access_id_to_acl
from django.utils.text import slugify


class StatusUpdateTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)

        self.statusPublic = StatusUpdate.objects.create(
            title="Test public event",
            description="Description",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
        )

        self.statusPrivate = StatusUpdate.objects.create(
            title="Test private event",
            description="Description",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
        )

        self.query = """
            fragment StatusUpdateParts on StatusUpdate {
                title
                description
                richDescription
                timeCreated
                timeUpdated
                accessId
                writeAccessId
                canEdit
                tags
                url
                inGroup
                group {
                    guid
                }
                views
                votes
                hasVoted
                isBookmarked
                isFollowing
                canBookmark
                canComment
                canVote
            }
            query GetStatusUpdat($guid: String!) {
                entity(guid: $guid) {
                    guid
                    status
                    ...StatusUpdateParts
                }
            }
        """

    def tearDown(self):
        self.statusPublic.delete()
        self.statusPrivate.delete()
        self.authenticatedUser.delete()

    def test_status_update_anonymous(self):

        request = HttpRequest()
        request.user = self.anonymousUser

        variables = {
            "guid": self.statusPublic.guid
        }

        result = graphql_sync(schema, { "query": self.query , "variables": variables}, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"]["guid"], self.statusPublic.guid)
        self.assertEqual(data["entity"]["title"], self.statusPublic.title)
        self.assertEqual(data["entity"]["description"], self.statusPublic.description)
        self.assertEqual(data["entity"]["richDescription"], self.statusPublic.rich_description)
        self.assertEqual(data["entity"]["accessId"], 2)
        self.assertEqual(data["entity"]["timeCreated"], str(self.statusPublic.created_at))
        self.assertEqual(data["entity"]["tags"], [])
        self.assertEqual(data["entity"]["views"], 0)
        self.assertEqual(data["entity"]["votes"], 0)
        self.assertEqual(data["entity"]["hasVoted"], False)
        self.assertEqual(data["entity"]["isBookmarked"], False)
        self.assertEqual(data["entity"]["isFollowing"], False)
        self.assertEqual(data["entity"]["canBookmark"], False)
        self.assertEqual(data["entity"]["canComment"], False)
        self.assertEqual(data["entity"]["canEdit"], False)
        self.assertEqual(data["entity"]["canVote"], False)
        self.assertEqual(data["entity"]["url"], "#{}".format(self.statusPublic.guid))

        variables = {
            "guid": self.statusPrivate.guid
        }

        result = graphql_sync(schema, { "query": self.query , "variables": variables}, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"], None)

    def test_status_update_private(self):
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {
            "guid": self.statusPrivate.guid
        }

        result = graphql_sync(schema, { "query": self.query , "variables": variables}, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"]["guid"], self.statusPrivate.guid)
        self.assertEqual(data["entity"]["title"], self.statusPrivate.title)
        self.assertEqual(data["entity"]["description"], self.statusPrivate.description)
        self.assertEqual(data["entity"]["richDescription"], self.statusPrivate.rich_description)
        self.assertEqual(data["entity"]["accessId"], 0)
        self.assertEqual(data["entity"]["timeCreated"], str(self.statusPrivate.created_at))
        self.assertEqual(data["entity"]["tags"], [])
        self.assertEqual(data["entity"]["tags"], [])
        self.assertEqual(data["entity"]["views"], 0)
        self.assertEqual(data["entity"]["votes"], 0)
        self.assertEqual(data["entity"]["hasVoted"], False)
        self.assertEqual(data["entity"]["isBookmarked"], False)
        self.assertEqual(data["entity"]["isFollowing"], False)
        self.assertEqual(data["entity"]["canBookmark"], True)
        self.assertEqual(data["entity"]["canComment"], True)
        self.assertEqual(data["entity"]["canVote"], True)
        self.assertEqual(data["entity"]["canEdit"], True)
