import json
from django.utils import timezone
from django.contrib.auth.models import AnonymousUser
from core.models.attachment import Attachment
from core.models import Group
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from blog.models import Blog
from news.models import News
from mixer.backend.django import mixer


class AddBlogTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)
        self.admin = mixer.blend(User, roles=['ADMIN'])
        self.group = mixer.blend(Group, owner=self.authenticatedUser, is_membership_on_request=False)
        self.group.join(self.authenticatedUser, 'owner')
        self.suggestedBlog = mixer.blend(Blog)
        self.suggestedNews = mixer.blend(News)

        self.data = {
            "input": {
                "type": "object",
                "subtype": "blog",
                "title": "My first Blog",
                "richDescription": "richDescription",
                "timePublished": str(timezone.localtime()),
                "scheduleArchiveEntity": str(timezone.localtime() + timezone.timedelta(days=10)),
                "scheduleDeleteEntity": str(timezone.localtime() + timezone.timedelta(days=20)),
                "accessId": 0,
                "writeAccessId": 0,
                "tags": ["tag1", "tag2"],
                "isRecommended": True,
                "suggestedItems": [self.suggestedBlog.guid, self.suggestedNews.guid]
            }
        }
        self.mutation = """
            fragment BlogParts on Blog {
                title
                richDescription
                timeCreated
                timeUpdated
                timePublished
                scheduleArchiveEntity
                scheduleDeleteEntity
                accessId
                writeAccessId
                canEdit
                tags
                url
                statusPublished
                inGroup
                group {
                    guid
                }
                isRecommended
                suggestedItems {
                    guid
                }
            }
            mutation ($input: addEntityInput!) {
                addEntity(input: $input) {
                    entity {
                    guid
                    status
                    ...BlogParts
                    }
                }
            }
        """

    def test_add_blog(self):
        variables = self.data

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result["data"]['addEntity']['entity']

        self.assertEqual(entity["title"], variables["input"]["title"])
        self.assertEqual(entity["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(entity["tags"], variables["input"]["tags"])
        self.assertEqual(entity["isRecommended"], False)
        self.assertEqual(entity["statusPublished"], 'published')
        self.assertDateEqual(entity["timePublished"], variables['input']['timePublished'])
        self.assertDateEqual(entity["scheduleArchiveEntity"], variables['input']['scheduleArchiveEntity'])
        self.assertDateEqual(entity["scheduleDeleteEntity"], variables['input']['scheduleDeleteEntity'])
        self.assertEqual(entity["suggestedItems"][0]["guid"], self.suggestedBlog.guid)
        self.assertEqual(entity["suggestedItems"][1]["guid"], self.suggestedNews.guid)

    def test_add_blog_admin(self):
        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, self.data)
        data = result["data"]

        self.assertEqual(data["addEntity"]["entity"]["title"], self.data["input"]["title"])
        self.assertEqual(data["addEntity"]["entity"]["richDescription"], self.data["input"]["richDescription"])
        self.assertEqual(data["addEntity"]["entity"]["tags"], self.data["input"]["tags"])
        self.assertEqual(data["addEntity"]["entity"]["isRecommended"], True)

    def test_add_blog_to_group(self):
        variables = self.data
        variables["input"]["containerGuid"] = self.group.guid

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, variables)

        data = result["data"]
        self.assertEqual(data["addEntity"]["entity"]["title"], variables["input"]["title"])
        self.assertEqual(data["addEntity"]["entity"]["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(data["addEntity"]["entity"]["inGroup"], True)
        self.assertEqual(data["addEntity"]["entity"]["group"]["guid"], self.group.guid)

    def test_add_unpublished_blog_admin(self):
        variables = {
            "input": {
                "type": "object",
                "subtype": "blog",
                "title": "My first Blog",
                "richDescription": "richDescription",
                "accessId": 0,
                "writeAccessId": 0,
                "tags": ["tag1", "tag2"],
                "isRecommended": True,
                "timePublished": None
            }
        }
        mutation = """
            fragment BlogParts on Blog {
                title
                richDescription
                timeCreated
                timeUpdated
                accessId
                writeAccessId
                canEdit
                tags
                url
                inGroup
                timePublished
                statusPublished
                group {
                    guid
                }
                isRecommended
            }
            mutation ($input: addEntityInput!) {
                addEntity(input: $input) {
                    entity {
                    guid
                    status
                    ...BlogParts
                    }
                }
            }
        """

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertEqual(data["addEntity"]["entity"]["title"], variables["input"]["title"])
        self.assertEqual(data["addEntity"]["entity"]["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(data["addEntity"]["entity"]["tags"], variables["input"]["tags"])
        self.assertEqual(data["addEntity"]["entity"]["isRecommended"], True)
        self.assertEqual(data["addEntity"]["entity"]["timePublished"], None)
        self.assertEqual(data["addEntity"]["entity"]["statusPublished"], 'draft')

    def test_add_minimal_entity(self):
        variables = {
            'input': {
                'title': "Simple blog",
                'subtype': "blog",
            }
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result["data"]["addEntity"]["entity"]
        self.assertTrue(entity['canEdit'])

    def test_add_with_attachment(self):
        attachment = mixer.blend(Attachment)

        variables = self.data
        variables["input"]["richDescription"] = json.dumps(
            {'type': 'file', 'attrs': {'url': f"/attachment/entity/{attachment.id}"}})

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result["data"]["addEntity"]["entity"]
        blog = Blog.objects.get(id=entity["guid"])
        self.assertTrue(blog.attachments.filter(id=attachment.id).exists())