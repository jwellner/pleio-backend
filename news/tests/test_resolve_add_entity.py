from django.utils import timezone
from core.tests.helpers import PleioTenantTestCase
from news.models import News
from user.models import User
from core.constances import USER_ROLES
from mixer.backend.django import mixer


class AddNewsTestCase(PleioTenantTestCase):

    def setUp(self):
        super(AddNewsTestCase, self).setUp()

        self.authenticatedUser = mixer.blend(User)
        self.adminUser = mixer.blend(User, roles=[USER_ROLES.ADMIN])
        self.editorUser = mixer.blend(User, roles=[USER_ROLES.EDITOR])
        self.relatedNews1 = mixer.blend(News)
        self.relatedNews2 = mixer.blend(News)

        self.data = {
            "input": {
                "type": "object",
                "subtype": "news",
                "title": "My first News",
                "richDescription": "richDescription",
                "accessId": 0,
                "writeAccessId": 0,
                "tags": ["tag1", "tag2"],
                "isFeatured": True,
                "source": "https://www.pleio.nl",
                "timePublished": str(timezone.localtime()),
                "scheduleArchiveEntity": str(timezone.localtime() + timezone.timedelta(days=10)),
                "scheduleDeleteEntity": str(timezone.localtime() + timezone.timedelta(days=20)),
                "relatedItems": [self.relatedNews1.guid, self.relatedNews2.guid]
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
                relatedItems {
                    edges {
                        guid
                    }
                }
            }
            mutation ($input: addEntityInput!) {
                addEntity(input: $input) {
                    entity {
                    guid
                    status
                    ...NewsParts
                    }
                }
            }
        """

    def test_add_news(self):
        variables = self.data

        self.graphql_client.force_login(self.authenticatedUser)
        with self.assertGraphQlError("could_not_add"):
            self.graphql_client.post(self.mutation, variables)

        self.assertEqual(self.graphql_client.result["data"]["addEntity"], None)

    def test_add_news_admin(self):
        variables = self.data

        self.graphql_client.force_login(self.adminUser)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result["data"]["addEntity"]["entity"]
        self.assertEqual(entity["title"], variables["input"]["title"])
        self.assertEqual(entity["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(entity["tags"], variables["input"]["tags"])
        self.assertEqual(entity["isFeatured"], True)
        self.assertEqual(entity["source"], variables["input"]["source"])
        self.assertDateEqual(entity["timePublished"], variables['input']['timePublished'])
        self.assertDateEqual(entity["scheduleArchiveEntity"], variables['input']['scheduleArchiveEntity'])
        self.assertDateEqual(entity["scheduleDeleteEntity"], variables['input']['scheduleDeleteEntity'])
        self.assertEqual(entity["relatedItems"]["edges"][0]["guid"], self.relatedNews1.guid)
        self.assertEqual(entity["relatedItems"]["edges"][1]["guid"], self.relatedNews2.guid)

    def test_add_news_editor(self):
        variables = self.data

        self.graphql_client.force_login(self.editorUser)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result["data"]["addEntity"]["entity"]
        self.assertEqual(entity["title"], variables["input"]["title"])
        self.assertEqual(entity["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(entity["tags"], variables["input"]["tags"])
        self.assertEqual(entity["isFeatured"], True)
        self.assertEqual(entity["source"], variables["input"]["source"])
        self.assertDateEqual(entity["timePublished"], variables['input']['timePublished'])
        self.assertDateEqual(entity["scheduleArchiveEntity"], variables['input']['scheduleArchiveEntity'])
        self.assertDateEqual(entity["scheduleDeleteEntity"], variables['input']['scheduleDeleteEntity'])
        self.assertEqual(entity["relatedItems"]["edges"][0]["guid"], self.relatedNews1.guid)
        self.assertEqual(entity["relatedItems"]["edges"][1]["guid"], self.relatedNews2.guid)
