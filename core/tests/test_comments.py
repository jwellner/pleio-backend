from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from mixer.backend.django import mixer
from django.db import connection
from unittest import mock

from blog.models import Blog
from core.constances import ACCESS_TYPE
from core.models import Comment
from core.tests.helpers import PleioTenantTestCase
from user.models import User


class CommentTestCase(PleioTenantTestCase):

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

        self.comments = mixer.cycle(5).blend(Comment, owner=self.authenticatedUser, container=self.blogPublic)

        self.anonComment = Comment.objects.create(
            name="Anoniemptje",
            email="test@test.com",
            container=self.blogPublic,
            rich_description="Just testing 1"
        )

        self.lastComment = Comment.objects.create(
            owner=self.authenticatedUser,
            container=self.blogPublic,
            rich_description="Just testing 2"
        )

        self.lastCommentSub = Comment.objects.create(
            owner=self.authenticatedUser,
            container=self.lastComment,
            rich_description="reply to just testing 2"
        )

        self.mutation1 = """
            mutation ($input: editEntityInput!) {
                editEntity(input: $input) {
                    entity {
                        guid
                    }
                }
            }
        """

        self.mutation2 = """
            mutation ($input: deleteEntityInput!) {
                deleteEntity(input: $input) {
                    success
                }
            }
        """

    def tearDown(self):
        super().tearDown()

    def test_blog_anonymous(self):
        query = """
            fragment BlogParts on Blog {
                title
                commentCount
                comments {
                    guid
                    richDescription
                    ownerName
                    canComment
                    commentCount
                    comments {
                        guid
                        richDescription
                        ownerName
                        canComment
                    }
                }
            }
            query GetBlog($guid: String!) {
                entity(guid: $guid) {
                    guid
                    status
                    ...BlogParts
                }
            }
        """

        variables = {
            "guid": self.blogPublic.guid
        }

        result = self.graphql_client.post(query, variables)

        data = result["data"]

        self.assertEqual(data["entity"]["guid"], self.blogPublic.guid)
        self.assertEqual(data["entity"]["commentCount"], 8)
        # first should be last added comment
        self.assertEqual(data["entity"]["comments"][0]['guid'], self.lastComment.guid)
        self.assertEqual(data["entity"]["comments"][0]['ownerName'], self.lastComment.owner.name)
        self.assertEqual(data["entity"]["comments"][0]['richDescription'], self.lastComment.rich_description)
        self.assertEqual(data["entity"]["comments"][0]['canComment'], False)
        self.assertEqual(data["entity"]["comments"][1]['ownerName'], self.anonComment.name)

    def test_comment_on_comment(self):
        query = """
            fragment BlogParts on Blog {
                title
                commentCount
                comments {
                    guid
                    richDescription
                    ownerName
                    commentCount
                    canComment
                    comments {
                        guid
                        richDescription
                        ownerName
                        canComment
                    }
                }
            }
            query GetBlog($guid: String!) {
                entity(guid: $guid) {
                    guid
                    status
                    ...BlogParts
                }
            }
        """

        variables = {
            "guid": self.blogPublic.guid
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(query, variables)

        data = result["data"]

        self.assertEqual(data["entity"]["guid"], self.blogPublic.guid)
        self.assertEqual(data["entity"]["commentCount"], 8)
        # first should be last added comment
        self.assertEqual(data["entity"]["comments"][0]['guid'], self.lastComment.guid)
        self.assertEqual(data["entity"]["comments"][0]['ownerName'], self.lastComment.owner.name)
        self.assertEqual(data["entity"]["comments"][0]['canComment'], True)
        self.assertEqual(data["entity"]["comments"][0]['richDescription'], self.lastComment.rich_description)
        self.assertEqual(data["entity"]["comments"][0]['commentCount'], 1)
        self.assertEqual(data["entity"]["comments"][0]['comments'][0]['guid'], self.lastCommentSub.guid)
        self.assertEqual(data["entity"]["comments"][0]['comments'][0]['canComment'], False)
        self.assertEqual(data["entity"]["comments"][1]['ownerName'], self.anonComment.name)

    def test_edit_comment_not_logged_in(self):

        variables = {
            "input": {
                "guid": self.anonComment.guid
            }
        }

        with self.assertGraphQlError('not_logged_in'):
            self.graphql_client.post(self.mutation1, variables)

    def test_edit_comment_could_not_find(self):

        variables = {
            "input": {
                "guid": "43ee295a-5950-4330-8f0e-372f9f4caddf"
            }
        }

        with self.assertGraphQlError('could_not_find'):
            self.graphql_client.force_login(self.authenticatedUser)
            self.graphql_client.post(self.mutation1, variables)

    def test_edit_comment_could_not_save(self):

        variables = {
            "input": {
                "guid": self.anonComment.guid
            }
        }

        with self.assertGraphQlError('could_not_save'):
            self.graphql_client.force_login(self.authenticatedUser)
            self.graphql_client.post(self.mutation1, variables)

    def test_edit_comment(self):

        variables = {
            "input": {
                "guid": self.lastComment.guid,
                "richDescription": "test"
            }
        }

        self.graphql_client.force_login(self.authenticatedUser)
        self.graphql_client.post(self.mutation1, variables)

        self.lastComment.refresh_from_db()

        self.assertEqual(self.lastComment.rich_description, variables["input"]["richDescription"])

    def test_add_comment(self):
        blog = Blog.objects.create(
            title="Test public blog",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            is_recommended=True,
            group=None
        )

        mutation = """
            mutation ($input: addEntityInput!) {
                addEntity(input: $input) {
                    entity {
                        guid
                    }
                }
            }
        """
        variables = {
            "input": {
                "subtype": "comment",
                "containerGuid": blog.guid,
                "richDescription": ""
            }
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]

        self.assertEqual(blog.comments.count(), 1)

        # sub

        variables = {
            "input": {
                "subtype": "comment",
                "containerGuid": data['addEntity']['entity']['guid'],
                "richDescription": ""
            }
        }
        
        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]

        self.assertEqual(blog.comments.count(), 1)
        self.assertEqual(blog.comments.first().comments.count(), 1)

        # sub sub comments

        variables = {
            "input": {
                "subtype": "comment",
                "containerGuid": data['addEntity']['entity']['guid'],
                "richDescription": ""
            }
        }

        with self.assertGraphQlError('could_not_add'):
            self.graphql_client.force_login(self.authenticatedUser)
            self.graphql_client.post(mutation, variables)

        self.assertEqual(blog.comments.count(), 1)
        self.assertEqual(blog.comments.first().comments.count(), 1)
        self.assertEqual(blog.comments.first().comments.first().comments.count(), 0)

    def test_flat_comment_list(self):
        owner = mixer.blend(User)
        # Blog, or any other comment containing entity.
        instance = Blog.objects.create(owner=owner,
                                       title="Title",
                                       rich_description="Bla",
                                       read_access=[ACCESS_TYPE.public],
                                       published=timezone.now() - timezone.timedelta(days=-1))
        # Normal comment.
        c1 = Comment.objects.create(container=instance,
                                    owner=owner)
        # Nested comment.
        Comment.objects.create(container=c1,
                               owner=owner)

        query = """
        query GetCommentCount($query: String!) {
          entity(guid: $query) {
            guid
            ... on Blog {
              commentCount
            }
            __typename
          }
        }
        """
        variables = {
            'query': instance.guid
        }

        self.graphql_client.force_login(owner)
        result = self.graphql_client.post(query, variables)

        self.assertEqual(result['data']['entity']['commentCount'], 2)

    def test_delete_comment_not_logged_in(self):

        variables = {
            "input": {
                "guid": self.anonComment.guid
            }
        }

        with self.assertGraphQlError('not_logged_in'):
            self.graphql_client.post(self.mutation2, variables)

    def test_delete_comment_could_not_find(self):

        variables = {
            "input": {
                "guid": "43ee295a-5950-4330-8f0e-372f9f4caddf"
            }
        }

        with self.assertGraphQlError('could_not_find'):
            self.graphql_client.force_login(self.authenticatedUser)
            self.graphql_client.post(self.mutation2, variables)

    def test_delete_comment_could_not_save(self):

        variables = {
            "input": {
                "guid": self.anonComment.guid
            }
        }

        with self.assertGraphQlError('could_not_save'):
            self.graphql_client.force_login(self.authenticatedUser)
            self.graphql_client.post(self.mutation2, variables)

    def test_delete_comment(self):

        variables = {
            "input": {
                "guid": self.lastComment.guid
            }
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation2, variables)

        self.assertTrue(result["data"]["deleteEntity"]["success"])


    @mock.patch('core.tasks.create_notification.delay')
    def test_notification_send(self, mocked_create_notification):
        self.comment1 = Comment.objects.create(
            owner=self.authenticatedUser,
            container=self.blogPublic
        )

        mocked_create_notification.assert_called_once_with(connection.schema_name, 'commented', 'blog.blog', self.blogPublic.id, self.comment1.owner.id)
