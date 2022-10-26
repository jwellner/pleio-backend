import json
from django.utils import timezone
from core.tests.helpers import PleioTenantTestCase
from core.models.attachment import Attachment
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
                "suggestedItems": [self.relatedNews1.guid, self.relatedNews2.guid]
            }
        }
        self.minimal_data = {
            'input': {
                'title': "Simple news",
                'subtype': "news",
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
                suggestedItems {
                    guid
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
        with self.assertGraphQlError("could_not_add"):
            self.graphql_client.force_login(self.authenticatedUser)
            self.graphql_client.post(self.mutation, self.data)

        self.assertEqual(self.graphql_client.result["data"]["addEntity"], None)

    def test_add_news_as_authorized_user(self):
        variables = self.data

        for user, msg in ((self.adminUser, "as admin"),
                          (self.editorUser, "as editor")):

            self.graphql_client.force_login(user)
            result = self.graphql_client.post(self.mutation, variables)

            entity = result["data"]["addEntity"]["entity"]
            self.assertEqual(entity["title"], variables["input"]["title"], msg=msg)
            self.assertEqual(entity["richDescription"], variables["input"]["richDescription"], msg=msg)
            self.assertEqual(entity["tags"], variables["input"]["tags"], msg=msg)
            self.assertEqual(entity["isFeatured"], True, msg=msg)
            self.assertEqual(entity["source"], variables["input"]["source"], msg=msg)
            self.assertDateEqual(entity["timePublished"], variables['input']['timePublished'], msg=msg)
            self.assertDateEqual(entity["scheduleArchiveEntity"], variables['input']['scheduleArchiveEntity'], msg=msg)
            self.assertDateEqual(entity["scheduleDeleteEntity"], variables['input']['scheduleDeleteEntity'], msg=msg)
            self.assertEqual(entity["suggestedItems"][0]["guid"], self.relatedNews1.guid, msg=msg)
            self.assertEqual(entity["suggestedItems"][1]["guid"], self.relatedNews2.guid, msg=msg)

    def test_add_minimal_entity(self):
        for user, msg in ((self.editorUser, "Error for Editors"),
                          (self.adminUser, "Error for Administrators")):
            self.graphql_client.force_login(user)
            result = self.graphql_client.post(self.mutation, self.minimal_data)
            entity = result["data"]["addEntity"]["entity"]

            self.assertTrue(entity['canEdit'], msg=msg)

    def test_add_minimal_entity_as_regular_user(self):
        with self.assertGraphQlError('could_not_add'):
            self.graphql_client.force_login(self.authenticatedUser)
            self.graphql_client.post(self.mutation, self.minimal_data)

    def test_add_with_attachment(self):
        attachment = mixer.blend(Attachment)

        variables = self.data
        variables["input"]["richDescription"] = json.dumps(
            {'type': 'file', 'attrs': {'url': f"/attachment/entity/{attachment.id}"}})

        self.graphql_client.force_login(self.editorUser)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result["data"]["addEntity"]["entity"]
        news = News.objects.get(id=entity["guid"])
        self.assertTrue(news.attachments.filter(id=attachment.id).exists())