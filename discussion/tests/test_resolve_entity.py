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
from discussion.models import Discussion
from mixer.backend.django import mixer
from core.constances import ACCESS_TYPE
from core.lib import get_acl, access_id_to_acl
from django.utils.text import slugify


class EventTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)

        self.discussionPublic = Discussion.objects.create(
            title="Test public event",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
        )

        self.discussionPrivate = Discussion.objects.create(
            title="Test private event",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            is_featured=True
        )

        self.query = """
            fragment DiscussionParts on Discussion {
                title
                richDescription
                timeCreated
                timeUpdated
                accessId
                writeAccessId
                canEdit
                tags
                featured {
                    image
                    video
                    videoTitle
                    positionY
                    alt
                }
                url
                inGroup
                group {
                    guid
                }
                isFeatured
            }
            query GetDiscussion($guid: String!) {
                entity(guid: $guid) {
                    guid
                    status
                    ...DiscussionParts
                }
            }
        """

    def tearDown(self):
        self.discussionPublic.delete()
        self.discussionPrivate.delete()
        self.authenticatedUser.delete()

    def test_event_anonymous(self):

        request = HttpRequest()
        request.user = self.anonymousUser

        variables = {
            "guid": self.discussionPublic.guid
        }

        result = graphql_sync(schema, { "query": self.query , "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"]["guid"], self.discussionPublic.guid)
        self.assertEqual(data["entity"]["title"], self.discussionPublic.title)
        self.assertEqual(data["entity"]["richDescription"], self.discussionPublic.rich_description)
        self.assertEqual(data["entity"]["accessId"], 2)
        self.assertEqual(data["entity"]["timeCreated"], self.discussionPublic.created_at.isoformat())
        self.assertEqual(data["entity"]["tags"], [])
        self.assertEqual(data["entity"]["canEdit"], False)
        self.assertEqual(data["entity"]["url"], "/discussion/view/{}/{}".format(self.discussionPublic.guid, slugify(self.discussionPublic.title)))
        self.assertEqual(data["entity"]["isFeatured"], self.discussionPublic.is_featured)

        variables = {
            "guid": self.discussionPrivate.guid
        }

        result = graphql_sync(schema, { "query": self.query , "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"], None)

    def test_event_private(self):
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {
            "guid": self.discussionPrivate.guid
        }

        result = graphql_sync(schema, { "query": self.query , "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"]["guid"], self.discussionPrivate.guid)
        self.assertEqual(data["entity"]["title"], self.discussionPrivate.title)
        self.assertEqual(data["entity"]["richDescription"], self.discussionPrivate.rich_description)
        self.assertEqual(data["entity"]["accessId"], 0)
        self.assertEqual(data["entity"]["timeCreated"], self.discussionPrivate.created_at.isoformat())
        self.assertEqual(data["entity"]["tags"], [])
        self.assertEqual(data["entity"]["canEdit"], True)
        self.assertEqual(data["entity"]["url"], "/discussion/view/{}/{}".format(self.discussionPrivate.guid, slugify(self.discussionPrivate.title)))
        self.assertEqual(data["entity"]["isFeatured"], self.discussionPrivate.is_featured)
