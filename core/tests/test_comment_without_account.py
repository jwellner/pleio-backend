from django.db import connection
from django_tenants.test.client import TenantClient
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from django.core.cache import cache
from core.models import Comment, CommentRequest
from user.models import User
from blog.models import Blog
from mixer.backend.django import mixer
from core.constances import ACCESS_TYPE
from unittest import mock

class CommentWithoutAccountTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)

        self.blogPublic = Blog.objects.create(
            title="Test public blog",
            description="Description",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            is_recommended=True,
            group=None
        )

        self.comments = mixer.cycle(1).blend(Comment, owner=self.authenticatedUser, container=self.blogPublic)

        cache.set("%s%s" % (connection.schema_name, 'COMMENT_WITHOUT_ACCOUNT_ENABLED'), True)
        cache.set("%s%s" % (connection.schema_name, 'IS_CLOSED'), False)

        self.client = TenantClient(self.tenant)

    def tearDown(self):
        self.blogPublic.delete()
        self.authenticatedUser.delete()
    
    def test_add_comment_disabled(self):
        cache.set("%s%s" % (connection.schema_name, 'COMMENT_WITHOUT_ACCOUNT_ENABLED'), False)

        mutation = """
            mutation ($input: addCommentWithoutAccountInput!) {
                addCommentWithoutAccount(input: $input) {
                    success
                }
            }
        """
        variables = { 
            "input": {
                "containerGuid": self.blogPublic.guid,
                "email": "test@test.com",
                "name": "Unit Tester",
                "description": "Yolo!",
                "richDescription": ""
            }
        }

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_add")

    def test_add_comment_invalidmail(self):

        mutation = """
            mutation ($input: addCommentWithoutAccountInput!) {
                addCommentWithoutAccount(input: $input) {
                    success
                }
            }
        """
        variables = { 
            "input": {
                "containerGuid": self.blogPublic.guid,
                "email": "xxxx",
                "name": "Unit Tester",
                "description": "Yolo!",
                "richDescription": ""
            }
        }

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "invalid_email")

    #@mock.patch('core.resolvers.mutation_add_comment_without_account.send_mail_multi.delay')
    def test_add_comment(self): #mocked_send_mail_multi

        mutation = """
            mutation ($input: addCommentWithoutAccountInput!) {
                addCommentWithoutAccount(input: $input) {
                    success
                }
            }
        """
        variables = { 
            "input": {
                "containerGuid": self.blogPublic.guid,
                "email": "test@test.com",
                "name": "Unit Tester",
                "description": "Yolo!",
                "richDescription": ""
            }
        }

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        # check request
        self.assertEqual(data["addCommentWithoutAccount"]["success"], True)

        #mocked_send_mail_multi.assert_called_once()

        comment_request = CommentRequest.objects.filter(email="test@test.com").first()

        self.assertEqual(comment_request.name, "Unit Tester")
        self.assertEqual(comment_request.container, self.blogPublic)
        
        confirm_url = '/comment/confirm/' + self.blogPublic.guid + '?email=' + comment_request.email + '&code=' + comment_request.code

        response = self.client.get(confirm_url, follow=True)

        self.assertRedirects(response, self.blogPublic.url)

        # commentRequest should be deleted
        comment_request = CommentRequest.objects.filter(email="test@test.com").first()
        self.assertEqual(comment_request, None)

        # comment should exists
        comment = self.blogPublic.comments.first()

        self.assertEqual(comment.owner, None)
        self.assertEqual(comment.description, "Yolo!")
        self.assertEqual(comment.email, "test@test.com")
        self.assertEqual(comment.name, "Unit Tester")

