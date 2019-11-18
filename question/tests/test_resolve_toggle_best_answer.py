from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import User, Group, Comment
from question.models import Question
from mixer.backend.django import mixer
from core.constances import ACCESS_TYPE
from core.lib import get_acl, access_id_to_acl
from django.utils.text import slugify

class ToggleIsClosedTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)

        self.question = Question.objects.create(
            title="Test1",
            description="Description",
            rich_description="",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            is_closed=False
        )

        self.answer = Comment.objects.create(
            description="Answer",
            rich_description="",
            owner=self.authenticatedUser,
            container=self.question
        )

    def tearDown(self):
        self.question.delete()
        self.authenticatedUser.delete()
    
    def test_toggle_best_answer(self):

        query = """
            mutation ($input: toggleBestAnswerInput!) {
                toggleBestAnswer(input: $input) {
                    entity {
                        guid
                        comments {
                            isBestAnswer
                        }
                    }
                }
            }
        """

        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {
            "input": {
                "guid": self.answer.guid,
            }
        }

        result = graphql_sync(schema, { "query": query , "variables": variables}, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]
       
        self.assertEqual(data["toggleBestAnswer"]["entity"]["guid"], self.question.guid)
        self.assertTrue(data["toggleBestAnswer"]["entity"]["comments"][0]["isBestAnswer"])

        self.question.refresh_from_db()

        self.assertEqual(self.question.best_answer, self.answer)

        variables = {
            "input": {
                "guid": self.answer.guid,
            }
        }

        result = graphql_sync(schema, { "query": query , "variables": variables}, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]
       
        self.assertEqual(data["toggleBestAnswer"]["entity"]["guid"], self.question.guid)
        self.assertFalse(data["toggleBestAnswer"]["entity"]["comments"][0]["isBestAnswer"])

        self.question.refresh_from_db()

        self.assertIsNone(self.question.best_answer)