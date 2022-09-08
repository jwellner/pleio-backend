from django.utils import timezone

from core.tests.helpers import PleioTenantTestCase
from user.models import User
from news.models import News
from core.constances import ACCESS_TYPE, USER_ROLES
from mixer.backend.django import mixer


class EditNewsTestCase(PleioTenantTestCase):

    def setUp(self):
        super(EditNewsTestCase, self).setUp()
        self.authenticatedUser = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.editorUser = mixer.blend(User, roles=[USER_ROLES.EDITOR])
        self.admin = mixer.blend(User, roles=[USER_ROLES.ADMIN])

        self.news = News.objects.create(
            title="Test public news",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            is_featured=False
        )
        self.relatedNews1 = mixer.blend(News)
        self.relatedNews2 = mixer.blend(News)

        self.data = {
            "input": {
                "guid": self.news.guid,
                "title": "My first News item",
                "richDescription": "richDescription",
                "accessId": 0,
                "writeAccessId": 0,
                "tags": ["tag1", "tag2"],
                "isFeatured": True,
                "source": "https://www.nos.nl",
                "timePublished": str(timezone.localtime()),
                "scheduleArchiveEntity": str(timezone.localtime() + timezone.timedelta(days=10)),
                "scheduleDeleteEntity": str(timezone.localtime() + timezone.timedelta(days=20)),
                "suggestedItems": [self.relatedNews1.guid, self.relatedNews2.guid]
            }
        }
        self.mutation = """
            fragment NewsParts on News {
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
                isFeatured
                source
                owner {
                    guid
                }
                suggestedItems {
                    guid
                }
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
                    ...NewsParts
                    }
                }
            }
        """

    def test_edit_news(self):
        variables = self.data

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result["data"]["editEntity"]["entity"]
        self.assertEqual(entity["title"], variables["input"]["title"])
        self.assertEqual(entity["richDescription"], variables["input"]['richDescription']) #rich_description is changed when published
        self.assertEqual(entity["tags"], variables["input"]["tags"])
        self.assertEqual(entity["isFeatured"], False) # Only editor or admin can set isFeatured
        self.assertEqual(entity["source"], variables["input"]["source"])
        self.assertDateEqual(entity["timePublished"], variables['input']['timePublished'])
        self.assertDateEqual(entity["scheduleArchiveEntity"], variables['input']['scheduleArchiveEntity'])
        self.assertDateEqual(entity["scheduleDeleteEntity"], variables['input']['scheduleDeleteEntity'])
        self.assertEqual(entity["suggestedItems"][0]["guid"], self.relatedNews1.guid)
        self.assertEqual(entity["suggestedItems"][1]["guid"], self.relatedNews2.guid)

        self.news.refresh_from_db()

        self.assertEqual(entity["title"], self.news.title)
        self.assertEqual(entity["richDescription"], self.news.rich_description)
        self.assertEqual(entity["tags"], self.news.tags)
        self.assertEqual(entity["isFeatured"], self.news.is_featured)
        self.assertEqual(entity["source"], self.news.source)
        self.assertDateEqual(entity["timePublished"], str(self.news.published))
        self.assertDateEqual(entity["scheduleArchiveEntity"], str(self.news.schedule_archive_after))
        self.assertDateEqual(entity["scheduleDeleteEntity"], str(self.news.schedule_delete_after))

    def test_edit_news_draft(self):
        self.data['draft'] = True

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, self.data)
        entity = result["data"]["editEntity"]["entity"]

        # Not stored on the entity.
        self.assertNotEqual(entity['richDescription'], self.data['input']['richDescription'])

        # But at the revision.
        self.assertEqual(entity['revision']['content']['richDescription'], self.data['input']['richDescription'])

    def test_edit_news_editor(self):
        variables = self.data
        variables["input"]["title"] = "Update door editor"

        self.graphql_client.force_login(self.editorUser)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result["data"]["editEntity"]["entity"]
        self.assertEqual(entity["title"], variables["input"]["title"])
        self.assertEqual(entity["richDescription"], variables["input"]['richDescription'])
        self.assertEqual(entity["tags"], variables["input"]["tags"])
        self.assertEqual(entity["isFeatured"], True)
        self.assertEqual(entity["source"], variables["input"]["source"])
        self.assertEqual(entity["owner"]["guid"], self.authenticatedUser.guid)
        self.assertEqual(entity["timeCreated"], self.news.created_at.isoformat())

        self.news.refresh_from_db()

        self.assertEqual(entity["title"], self.news.title)
        self.assertEqual(entity["richDescription"], self.news.rich_description)
        self.assertEqual(entity["tags"], self.news.tags)
        self.assertEqual(entity["isFeatured"], self.news.is_featured)
        self.assertEqual(entity["source"], self.news.source)
        self.assertEqual(entity["owner"]["guid"], self.authenticatedUser.guid)
        self.assertEqual(entity["timeCreated"], self.news.created_at.isoformat())

    def test_edit_news_admin(self):
        variables = self.data
        variables["input"]["timeCreated"] = "2018-12-10T23:00:00.000Z"
        variables["input"]["ownerGuid"] = self.user2.guid

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result["data"]["editEntity"]["entity"]
        self.assertEqual(entity["richDescription"], variables["input"]['richDescription'])
        self.assertEqual(entity["tags"], variables["input"]["tags"])
        self.assertEqual(entity["isFeatured"], True)
        self.assertEqual(entity["source"], variables["input"]["source"])
        self.assertEqual(entity["owner"]["guid"], self.user2.guid)
        self.assertEqual(entity["timeCreated"], "2018-12-10T23:00:00+00:00")

        self.news.refresh_from_db()

        self.assertEqual(entity["title"], self.news.title)
        self.assertEqual(entity["richDescription"], self.news.rich_description)
        self.assertEqual(entity["tags"], self.news.tags)
        self.assertEqual(entity["isFeatured"], self.news.is_featured)
        self.assertEqual(entity["source"], self.news.source)
        self.assertEqual(entity["owner"]["guid"], self.user2.guid)
        self.assertEqual(entity["timeCreated"], "2018-12-10T23:00:00+00:00")
