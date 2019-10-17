from django.db import connection
from django.test import TestCase
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

class ToggleIsClosedTestCase(TestCase):

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

    def tearDown(self):
        self.question.delete()
        self.authenticatedUser.delete()
    
    def test_toggle_is_closed(self):

        query = """
            mutation ($input: toggleIsClosedInput!) {
                toggleIsClosed(input: $input) {
                    entity {
                        guid
                        isClosed
                    }
                }
            }
        """

        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {
            "input": {
                "guid": self.question.guid,
            }
        }

        result = graphql_sync(schema, { "query": query , "variables": variables}, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]
       
        self.assertEqual(data["toggleIsClosed"]["entity"]["guid"], self.question.guid)
        self.assertTrue(data["toggleIsClosed"]["entity"]["isClosed"])

        self.question.refresh_from_db()

        self.assertTrue(self.question.is_closed)

        variables = {
            "input": {
                "guid": self.question.guid,
            }
        }

        result = graphql_sync(schema, { "query": query , "variables": variables}, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]
       
        self.assertEqual(data["toggleIsClosed"]["entity"]["guid"], self.question.guid)
        self.assertFalse(data["toggleIsClosed"]["entity"]["isClosed"])

        self.question.refresh_from_db()

        self.assertFalse(self.question.is_closed)