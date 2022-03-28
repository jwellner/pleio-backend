from django.utils import timezone
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Comment
from user.models import User
from blog.models import Blog
from mixer.backend.django import mixer
from core.constances import ACCESS_TYPE


class CommentTestCase(FastTenantTestCase):

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

    def tearDown(self):
        self.blogPublic.delete()
        self.authenticatedUser.delete()

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
        request = HttpRequest()
        request.user = self.anonymousUser

        variables = {
            "guid": self.blogPublic.guid
        }

        result = graphql_sync(schema, {"query": query, "variables": variables}, context_value={"request": request})

        self.assertTrue(result[0])

        data = result[1]["data"]

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
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {
            "guid": self.blogPublic.guid
        }

        result = graphql_sync(schema, {"query": query, "variables": variables}, context_value={"request": request})

        self.assertTrue(result[0])

        data = result[1]["data"]

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

        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={"request": request})

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(blog.comments.count(), 1)

        # sub

        variables = {
            "input": {
                "subtype": "comment",
                "containerGuid": data['addEntity']['entity']['guid'],
                "richDescription": ""
            }
        }
        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={"request": request})

        self.assertTrue(result[0])

        data = result[1]["data"]

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
        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={"request": request})

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_add")

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

        request = HttpRequest()
        request.user = owner
        success, result = graphql_sync(schema, {"query": query, "variables": variables},
                                       context_value={"request": request})

        self.assertEqual(result['data']['entity']['commentCount'], 2)
