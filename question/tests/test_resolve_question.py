from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import User, Group
from question.models import Question
from mixer.backend.django import mixer
from core.constances import ACCESS_TYPE
from core.lib import get_acl, access_id_to_acl
from django.utils.text import slugify

class QuestionTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)

        self.questionPublic = Question.objects.create(
            title="Test public question",
            description="Description",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            is_closed=False
        )

        self.questionPrivate = Question.objects.create(
            title="Test private question",
            description="Description",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            is_closed=False
        )

    def tearDown(self):
        self.questionPublic.delete()
        self.questionPrivate.delete()
        self.authenticatedUser.delete()
    
    def test_question_anonymous(self):

        query = """
            fragment QuestionParts on Question {
                title
                description
                richDescription
                accessId
                timeCreated
                featured {
                    image
                    video
                    positionY
                }
                canEdit
                tags
                url
                views
                votes
                hasVoted
                isBookmarked
                isFollowing
                isClosed
                canBookmark
                canComment
                canChooseBestAnswer
                comments {
                    guid
                    description
                    richDescription
                    isBestAnswer
                    canEdit
                    timeCreated
                    hasVoted
                    votes
                }
                owner {
                    guid
                }
                group {
                    guid
                }
            }
            query GetQuestion($guid: String!) {
                entity(guid: $guid) {
                    guid
                    status
                    ...QuestionParts
                }
            }
        """
        request = HttpRequest()
        request.user = self.anonymousUser

        variables = { 
            "guid": self.questionPublic.guid
        }

        result = graphql_sync(schema, { "query": query , "variables": variables}, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]
       
        self.assertEqual(data["entity"]["guid"], self.questionPublic.guid)
        self.assertEqual(data["entity"]["title"], self.questionPublic.title)
        self.assertEqual(data["entity"]["description"], self.questionPublic.description)
        self.assertEqual(data["entity"]["richDescription"], self.questionPublic.rich_description)
        self.assertEqual(data["entity"]["accessId"], 2)
        self.assertEqual(data["entity"]["timeCreated"], str(self.questionPublic.created_at))
        self.assertEqual(data["entity"]["isClosed"], self.questionPublic.is_closed)
        self.assertEqual(data["entity"]["tags"], [])
        self.assertEqual(data["entity"]["views"], 0)
        self.assertEqual(data["entity"]["votes"], 0)
        self.assertEqual(data["entity"]["hasVoted"], False)
        self.assertEqual(data["entity"]["isBookmarked"], False)
        self.assertEqual(data["entity"]["isFollowing"], False)
        self.assertEqual(data["entity"]["canBookmark"], False)
        self.assertEqual(data["entity"]["canEdit"], False)
        self.assertEqual(data["entity"]["canComment"], False)
        self.assertEqual(data["entity"]["canChooseBestAnswer"], False)
        self.assertEqual(data["entity"]["owner"]["guid"], self.questionPublic.owner.guid)
        self.assertEqual(data["entity"]["url"], "/questions/view/{}/{}".format(self.questionPublic.guid, slugify(self.questionPublic.title)))

        variables = { 
            "guid": self.questionPrivate.guid
        }

        result = graphql_sync(schema, { "query": query , "variables": variables}, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]
       
        self.assertEqual(data["entity"], None)
    
    def test_question_owner(self):

        query = """
            fragment QuestionParts on Question {
                title
                description
                richDescription
                accessId
                timeCreated
                featured {
                    image
                    video
                    positionY
                }
                canEdit
                tags
                url
                views
                votes
                hasVoted
                isBookmarked
                isFollowing
                isClosed
                canBookmark
                canComment
                canChooseBestAnswer
                comments {
                    guid
                    description
                    richDescription
                    isBestAnswer
                    canEdit
                    timeCreated
                    hasVoted
                    votes
                }
                owner {
                    guid
                }
                group {
                    guid
                }
            }
            query GetQuestion($guid: String!) {
                entity(guid: $guid) {
                    guid
                    status
                    ...QuestionParts
                }
            }
        """
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = { 
            "guid": self.questionPrivate.guid
        }

        result = graphql_sync(schema, { "query": query , "variables": variables}, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]
       
        self.assertEqual(data["entity"]["guid"], self.questionPrivate.guid)
        self.assertEqual(data["entity"]["title"], self.questionPrivate.title)
        self.assertEqual(data["entity"]["description"], self.questionPrivate.description)
        self.assertEqual(data["entity"]["richDescription"], self.questionPrivate.rich_description)
        self.assertEqual(data["entity"]["accessId"], 0)
        self.assertEqual(data["entity"]["timeCreated"], str(self.questionPrivate.created_at))
        self.assertEqual(data["entity"]["isClosed"], self.questionPrivate.is_closed)
        self.assertEqual(data["entity"]["tags"], [])
        self.assertEqual(data["entity"]["views"], 0)
        self.assertEqual(data["entity"]["votes"], 0)
        self.assertEqual(data["entity"]["hasVoted"], False)
        self.assertEqual(data["entity"]["isBookmarked"], False)
        self.assertEqual(data["entity"]["isFollowing"], False)
        self.assertEqual(data["entity"]["canBookmark"], True)
        self.assertEqual(data["entity"]["canEdit"], True)
        self.assertEqual(data["entity"]["canComment"], True)
        self.assertEqual(data["entity"]["canChooseBestAnswer"], True)
        self.assertEqual(data["entity"]["owner"]["guid"], self.questionPrivate.owner.guid)
        self.assertEqual(data["entity"]["url"], "/questions/view/{}/{}".format(self.questionPrivate.guid, slugify(self.questionPrivate.title)))
