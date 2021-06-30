from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from django.core.files import File
from django.conf import settings
from backend2.schema import schema
from ariadne import graphql_sync
from ariadne.file_uploads import combine_multipart_data, upload_scalar
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group, Comment, EntityAttachment, GroupAttachment, CommentAttachment
from user.models import User
from blog.models import Blog
from core.constances import ACCESS_TYPE
from mixer.backend.django import mixer
from graphql import GraphQLError
from unittest.mock import MagicMock, patch

class AddAttachmentTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)
        self.authenticatedUser2 = mixer.blend(User)

        self.mutation = """
            mutation addAttachment($input: addAttachmentInput!) {
                addAttachment(input: $input) {
                    attachment {      
                        id
                        url
                        mimeType
                        name
                    }
                }
            }
        """

    @patch("core.lib.get_mimetype")
    @patch("{}.open".format(settings.DEFAULT_FILE_STORAGE))
    def test_add_attachment_anonymous(self, mock_open, mock_mimetype):

        blog1 = Blog.objects.create(
            title="Blog logged_in",
            owner=self.authenticatedUser,
            read_access=[ACCESS_TYPE.logged_in],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)]
        )

        file_mock = MagicMock(spec=File)
        file_mock.name = 'test.gif'
        file_mock.content_type = 'image/gif'

        mock_open.return_value = file_mock
        mock_mimetype.return_value = file_mock.content_type

        variables = {
            "input": {
                "file": "test.gif",
                "contentGuid": blog1.guid
            }
        }

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, {"query": self.mutation, "variables": variables}, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")

    @patch("core.lib.get_mimetype")
    @patch("{}.open".format(settings.DEFAULT_FILE_STORAGE))
    def test_add_attachment_no_access(self, mock_open, mock_mimetype):

        blog1 = Blog.objects.create(
            title="Blog logged_in",
            owner=self.authenticatedUser,
            read_access=[ACCESS_TYPE.logged_in],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)]
        )

        file_mock = MagicMock(spec=File)
        file_mock.name = 'test.gif'
        file_mock.content_type = 'image/gif'

        mock_open.return_value = file_mock
        mock_mimetype.return_value = file_mock.content_type

        variables = {
            "input": {
                "file": "test.gif",
                "contentGuid": blog1.guid
            }
        }

        request = HttpRequest()
        request.user = self.authenticatedUser2

        result = graphql_sync(schema, {"query": self.mutation, "variables": variables}, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_add")

    @patch("core.lib.get_mimetype")
    @patch("{}.open".format(settings.DEFAULT_FILE_STORAGE))
    def test_add_attachment_to_entity(self, mock_open, mock_mimetype):

        blog1 = Blog.objects.create(
            title="Blog logged_in",
            owner=self.authenticatedUser,
            read_access=[ACCESS_TYPE.logged_in],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)]
        )

        file_mock = MagicMock(spec=File)
        file_mock.name = 'test.gif'
        file_mock.content_type = 'image/gif'

        mock_open.return_value = file_mock
        mock_mimetype.return_value = file_mock.content_type

        variables = {
            "input": {
                "file": "test.gif",
                "contentGuid": blog1.guid,
            }
        }

        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, {"query": self.mutation, "variables": variables}, context_value={ "request": request })

        data = result[1]["data"]

        attachment = blog1.attachments.first()

        self.assertEqual(data["addAttachment"]["attachment"]["id"], str(attachment.id))
        self.assertEqual(data["addAttachment"]["attachment"]["url"], attachment.url)
        self.assertEqual(data["addAttachment"]["attachment"]["mimeType"], attachment.mime_type)
        self.assertEqual(data["addAttachment"]["attachment"]["name"], file_mock.name)

        # add another attachment
        result = graphql_sync(schema, {"query": self.mutation, "variables": variables}, context_value={ "request": request })

        self.assertEqual(blog1.attachments.count(), 2)

        # delete blog and check if attachments are deleted
        self.assertEqual(EntityAttachment.objects.count(), 2)
        blog1.delete()
        self.assertEqual(EntityAttachment.objects.count(), 0)

    @patch("core.lib.get_mimetype")
    @patch("{}.open".format(settings.DEFAULT_FILE_STORAGE))
    def test_add_attachment_to_group(self, mock_open, mock_mimetype):

        group = mixer.blend(Group, owner=self.authenticatedUser)

        file_mock = MagicMock(spec=File)
        file_mock.name = 'test.gif'
        file_mock.content_type = 'image/gif'

        mock_open.return_value = file_mock
        mock_mimetype.return_value = file_mock.content_type

        variables = {
            "input": {
                "file": "test.gif",
                "contentGuid": group.guid
            }
        }

        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, {"query": self.mutation, "variables": variables}, context_value={ "request": request })

        data = result[1]["data"]

        attachment = group.attachments.first()

        self.assertEqual(data["addAttachment"]["attachment"]["id"], str(attachment.id))
        self.assertEqual(data["addAttachment"]["attachment"]["url"], attachment.url)
        self.assertEqual(data["addAttachment"]["attachment"]["mimeType"], attachment.mime_type)
        self.assertEqual(data["addAttachment"]["attachment"]["name"], file_mock.name)

        # add another attachment
        result = graphql_sync(schema, {"query": self.mutation, "variables": variables}, context_value={ "request": request })

        self.assertEqual(group.attachments.count(), 2)

        # delete blog and check if attachments are deleted
        self.assertEqual(GroupAttachment.objects.count(), 2)
        group.delete()
        self.assertEqual(GroupAttachment.objects.count(), 0)


    @patch("core.lib.get_mimetype")
    @patch("{}.open".format(settings.DEFAULT_FILE_STORAGE))
    def test_add_attachment_to_comment(self, mock_open, mock_mimetype):
        blog1 = Blog.objects.create(
            title="Blog logged_in",
            owner=self.authenticatedUser,
            read_access=[ACCESS_TYPE.logged_in],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)]
        )

        comment = Comment.objects.create(
            description="Comment",
            owner=self.authenticatedUser,
            container=blog1
        )

        file_mock = MagicMock(spec=File)
        file_mock.name = 'test.gif'
        file_mock.content_type = 'image/gif'

        mock_open.return_value = file_mock
        mock_mimetype.return_value = file_mock.content_type

        variables = {
            "input": {
                "file": "test.gif",
                "contentGuid": comment.guid
            }
        }

        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, {"query": self.mutation, "variables": variables}, context_value={ "request": request })

        data = result[1]["data"]

        attachment = comment.attachments.first()

        self.assertEqual(data["addAttachment"]["attachment"]["id"], str(attachment.id))
        self.assertEqual(data["addAttachment"]["attachment"]["url"], attachment.url)
        self.assertEqual(data["addAttachment"]["attachment"]["mimeType"], attachment.mime_type)
        self.assertEqual(data["addAttachment"]["attachment"]["name"], file_mock.name)

        # add another attachment
        result = graphql_sync(schema, {"query": self.mutation, "variables": variables}, context_value={ "request": request })

        self.assertEqual(comment.attachments.count(), 2)

        # delete blog and check if attachments are deleted
        self.assertEqual(CommentAttachment.objects.count(), 2)
        comment.delete()
        self.assertEqual(CommentAttachment.objects.count(), 0)
