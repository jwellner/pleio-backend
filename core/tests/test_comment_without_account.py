import uuid

from django.db import connection
from django.http import HttpRequest, Http404
from django_tenants.test.client import TenantClient
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from core.models import Comment, CommentRequest
from core.tests.helpers import PleioTenantTestCase, override_config
from core.views import comment_confirm
from user.models import User
from blog.models import Blog
from mixer.backend.django import mixer
from core.constances import ACCESS_TYPE
from unittest import mock


class CommentWithoutAccountTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)

        self.blogPublic = Blog.objects.create(
            title="Test public blog",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            is_recommended=True,
            group=None
        )

        self.comments = mixer.cycle(1).blend(Comment, owner=self.authenticatedUser, container=self.blogPublic)
        self.client = TenantClient(self.tenant)

    def tearDown(self):
        super().tearDown()

    @override_config(
        COMMENT_WITHOUT_ACCOUNT_ENABLED=False,
        IS_CLOSED=False
    )
    def test_add_comment_disabled(self):

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
                "richDescription": ""
            }
        }

        with self.assertGraphQlError("could_not_add"):
            self.graphql_client.post(mutation, variables)

    @override_config(
        COMMENT_WITHOUT_ACCOUNT_ENABLED=True,
        IS_CLOSED=False
    )
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
                "richDescription": ""
            }
        }

        with self.assertGraphQlError("invalid_email"):
            self.graphql_client.post(mutation, variables)

    @override_config(
        COMMENT_WITHOUT_ACCOUNT_ENABLED=True,
        IS_CLOSED=False
    )
    @mock.patch('core.resolvers.mutation_add_comment_without_account.schedule_comment_without_account_mail')
    def test_add_comment(self, mocked_mail):
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
                "richDescription": ""
            }
        }

        result = self.graphql_client.post(mutation, variables)
        data = result["data"]

        # check request
        self.assertEqual(data["addCommentWithoutAccount"]["success"], True)
        self.assertEqual(mocked_mail.call_count, 1)

        comment_request = CommentRequest.objects.filter(email="test@test.com").first()
        self.assertEqual(comment_request.name, "Unit Tester")
        self.assertEqual(comment_request.container, self.blogPublic)

        # TODO: Split the test here. Next is another (but related) functionality.

        confirm_url = '/comment/confirm/' + self.blogPublic.guid + '?email=' + comment_request.email + '&code=' + comment_request.code
        response = self.client.get(confirm_url, follow=True)

        self.assertRedirects(response, self.blogPublic.url)

        # commentRequest should be deleted
        comment_request = CommentRequest.objects.filter(email="test@test.com").first()
        self.assertEqual(comment_request, None)

        # comment should exists
        comment = self.blogPublic.comments.first()

        self.assertEqual(comment.owner, None)
        self.assertEqual(comment.email, "test@test.com")
        self.assertEqual(comment.name, "Unit Tester")

    @override_config(
        COMMENT_WITHOUT_ACCOUNT_ENABLED=True,
        IS_CLOSED=False
    )
    def test_confirm_comment_non_comment(self):
        request = HttpRequest()
        random_id = uuid.uuid4()

        with self.assertRaises(Http404):
            comment_confirm(request, random_id)
