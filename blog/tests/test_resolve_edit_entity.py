from core.models import Group
from core.tests.helpers import PleioTenantTestCase
from news.models import News
from user.models import User
from blog.models import Blog
from core.constances import ACCESS_TYPE, TEXT_TOO_LONG
from mixer.backend.django import mixer
from django.utils import timezone


class EditBlogTestCase(PleioTenantTestCase):

    def setUp(self):
        super(EditBlogTestCase, self).setUp()
        self.authenticatedUser = mixer.blend(User)
        self.user2 = mixer.blend(User)

        self.admin = mixer.blend(User)
        self.admin.roles = ['ADMIN']
        self.admin.save()

        self.group = mixer.blend(Group)
        self.blog = Blog.objects.create(
            title="Test public event",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            is_recommended=False
        )
        self.blog_multiple_read_access = Blog.objects.create(
            title="Test private blog",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id), ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            is_recommended=False
        )
        self.suggestedBlog = mixer.blend(Blog)
        self.suggestedNews = mixer.blend(News)

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
                timePublished
                statusPublished
                url
                inGroup
                group {
                    guid
                }
                owner {
                    guid
                }
                suggestedItems {
                    guid
                }
                isRecommended
                revision {
                    content {
                        richDescription
                    }
                }
            }
            mutation ($input: editEntityInput!, $draft: Boolean) {
                editEntity(input: $input, draft: $draft) {
                    entity {
                    guid
                    status
                    ...BlogParts
                    }
                }
            }
        """

        self.variables = {
            "input": {
                "guid": self.blog.guid,
                "title": "My first Event",
                "richDescription": "richDescription",
                "accessId": 0,
                "writeAccessId": 0,
                "tags": ["tag1", "tag2"],
                "isRecommended": True,
                "timeCreated": "2018-12-10T23:00:00.000Z",
                "groupGuid": self.group.guid,
                "ownerGuid": self.user2.guid
            }
        }

    def tearDown(self):
        self.blog.delete()
        self.authenticatedUser.delete()
        self.user2.delete()
        self.admin.delete()
        self.group.delete()

    def test_edit_blog(self):
        variables = {
            "input": {
                "guid": self.blog.guid,
                "title": "My first Event",
                "richDescription": "richDescription",
                "accessId": 0,
                "writeAccessId": 0,
                "tags": ["tag1", "tag2"],
                "isRecommended": True,
                "timeCreated": "2018-12-10T23:00:00.000Z",
                "groupGuid": self.group.guid,
                "ownerGuid": self.user2.guid,
                "timePublished": None,
                "scheduleArchiveEntity": str(timezone.localtime() + timezone.timedelta(days=10)),
                "scheduleDeleteEntity": str(timezone.localtime() + timezone.timedelta(days=20)),
                "suggestedItems": [self.suggestedBlog.guid, self.suggestedNews.guid]
            }
        }
        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result["data"]["editEntity"]["entity"]
        self.assertEqual(entity["title"], variables["input"]["title"])
        self.assertEqual(entity["richDescription"], variables['input']['richDescription'])
        self.assertEqual(entity["tags"], variables["input"]["tags"])
        self.assertEqual(entity["isRecommended"], False)  # only admin can set isRecommended
        self.assertEqual(entity["group"], None)
        self.assertEqual(entity["owner"]["guid"], self.authenticatedUser.guid)
        self.assertEqual(entity["timeCreated"], self.blog.created_at.isoformat())
        self.assertEqual(entity["statusPublished"], 'draft')
        self.assertEqual(entity["timePublished"], None)
        self.assertDateEqual(entity["scheduleArchiveEntity"], variables['input']['scheduleArchiveEntity'])
        self.assertDateEqual(entity["scheduleDeleteEntity"], variables['input']['scheduleDeleteEntity'])
        self.assertEqual(entity["suggestedItems"][0]["guid"], self.suggestedBlog.guid)
        self.assertEqual(entity["suggestedItems"][1]["guid"], self.suggestedNews.guid)

        self.blog.refresh_from_db()

        self.assertEqual(entity["title"], self.blog.title)
        self.assertEqual(entity["richDescription"], self.blog.rich_description)
        self.assertEqual(entity["tags"], self.blog.tags)
        self.assertEqual(entity["isRecommended"], self.blog.is_recommended)

    def test_edit_blog_draft(self):
        self.variables['draft'] = True

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, self.variables)
        entity = result['data']['editEntity']['entity']

        # not stored on the entity itself
        self.assertNotEqual(entity['richDescription'], self.variables['input']['richDescription'])

        # but in a revision
        self.assertEqual(entity['revision']['content']['richDescription'], self.variables['input']['richDescription'])

    def test_edit_blog_by_admin(self):
        variables = self.variables
        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result["data"]["editEntity"]["entity"]
        self.assertEqual(entity["title"], variables["input"]["title"])
        self.assertEqual(entity["richDescription"], variables['input']['richDescription'])
        self.assertEqual(entity["tags"], variables["input"]["tags"])
        self.assertEqual(entity["isRecommended"], True)
        self.assertEqual(entity["group"]["guid"], self.group.guid)
        self.assertEqual(entity["owner"]["guid"], self.user2.guid)
        self.assertEqual(entity["timeCreated"], "2018-12-10T23:00:00+00:00")

        self.blog.refresh_from_db()

        self.assertEqual(entity["title"], self.blog.title)
        self.assertEqual(entity["richDescription"], self.blog.rich_description)
        self.assertEqual(entity["tags"], self.blog.tags)
        self.assertEqual(entity["isRecommended"], self.blog.is_recommended)
        self.assertEqual(entity["group"]["guid"], self.group.guid)
        self.assertEqual(entity["owner"]["guid"], self.user2.guid)
        self.assertEqual(entity["statusPublished"], "published")
        self.assertEqual(entity["timeCreated"], "2018-12-10T23:00:00+00:00")

    def test_edit_blog_group_null_by_admin(self):
        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, self.variables)

        entity = result["data"]["editEntity"]["entity"]
        self.assertEqual(entity["group"]["guid"], self.group.guid)

        self.variables["input"]["groupGuid"] = None

        result = self.graphql_client.post(self.mutation, self.variables)
        entity = result["data"]["editEntity"]["entity"]

        self.assertIsNone(entity["group"])

    def test_edit_blog_set_future_published(self):
        variables = self.variables
        variables["input"]["timePublished"] = "4018-12-10T23:00:00.000Z"

        self.graphql_client.force_login(self.authenticatedUser)

        result = self.graphql_client.post(self.mutation, variables)
        entity = result["data"]["editEntity"]["entity"]

        self.assertEqual(entity["title"], variables["input"]["title"])
        self.assertEqual(entity["richDescription"], variables['input']['richDescription'])
        self.assertEqual(entity["tags"], variables["input"]["tags"])
        self.assertEqual(entity["isRecommended"], False)  # only admin can set isRecommended
        self.assertEqual(entity["group"], None)
        self.assertEqual(entity["owner"]["guid"], self.authenticatedUser.guid)
        self.assertEqual(entity["timeCreated"], self.blog.created_at.isoformat())
        self.assertEqual(entity["statusPublished"], 'draft')
        self.assertEqual(entity["timePublished"], "4018-12-10T23:00:00+00:00")

        self.blog.refresh_from_db()

        self.assertEqual(entity["title"], self.blog.title)
        self.assertEqual(entity["richDescription"], self.blog.rich_description)
        self.assertEqual(entity["tags"], self.blog.tags)
        self.assertEqual(entity["isRecommended"], self.blog.is_recommended)

    def test_edit_abstract(self):
        variables = {
            "input": {
                "guid": self.blog.guid,
                "abstract": "intro",
                "richDescription": "description",
            }
        }
        mutation = """
            fragment BlogParts on Blog {
                abstract
                excerpt
            }
            mutation ($input: editEntityInput!) {
                editEntity(input: $input) {
                    entity {
                    guid
                    status
                    ...BlogParts
                    }
                }
            }
        """

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(mutation, variables)

        entity = result["data"]["editEntity"]["entity"]
        self.assertEqual(entity["abstract"], "intro")
        self.assertEqual(entity["excerpt"], "intro")

    def test_edit_without_abstract(self):
        variables = {
            "input": {
                "guid": self.blog.guid,
                "richDescription": "description",
            }
        }
        mutation = """
            fragment BlogParts on Blog {
                abstract
                excerpt
            }
            mutation ($input: editEntityInput!) {
                editEntity(input: $input) {
                    entity {
                    guid
                    status
                    ...BlogParts
                    }
                }
            }
        """

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(mutation, variables)

        entity = result["data"]["editEntity"]["entity"]
        self.assertEqual(entity["abstract"], None)
        self.assertEqual(entity["excerpt"], variables['input']['richDescription'])

    def test_edit_abstract_too_long(self):
        variables = {
            "input": {
                "guid": self.blog.guid,
                "abstract": "x" * 321,
            }
        }
        mutation = """
            fragment BlogParts on Blog {
                abstract
                excerpt
            }
            mutation ($input: editEntityInput!) {
                editEntity(input: $input) {
                    entity {
                    guid
                    status
                    ...BlogParts
                    }
                }
            }
        """

        self.graphql_client.force_login(self.authenticatedUser)

        with self.assertGraphQlError(TEXT_TOO_LONG):
            self.graphql_client.post(mutation, variables)

    def test_edit_owner_of_blog_by_admin(self):
        variables = {
            "input": {
                "guid": self.blog_multiple_read_access.guid,
                "ownerGuid": self.user2.guid,
            }
        }

        mutation = """
            fragment BlogParts on Blog {
                owner {
                    guid
                }
            }
            mutation ($input: editEntityInput!) {
                editEntity(input: $input) {
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

        entity = result["data"]["editEntity"]["entity"]
        self.assertEqual(entity["owner"]["guid"], self.user2.guid)

        self.blog_multiple_read_access.refresh_from_db()
        self.assertEqual(self.blog_multiple_read_access.read_access, [ACCESS_TYPE.public, ACCESS_TYPE.user.format(self.user2.id)])
        self.assertEqual(self.blog_multiple_read_access.write_access, [ACCESS_TYPE.user.format(self.user2.id)])
