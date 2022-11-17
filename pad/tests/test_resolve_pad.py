from core.tests.helpers import PleioTenantTestCase
from user.models import User
from core.models.group import Group
from file.models import FileFolder
from mixer.backend.django import mixer
from core.constances import ACCESS_TYPE
from django.utils.text import slugify


class PadTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.authenticatedUser = mixer.blend(User)
        self.authenticatedAdminUser = mixer.blend(User, roles = ['ADMIN'])
        self.authenticatedNotGroupMember = mixer.blend(User)
        self.group = mixer.blend(Group, owner=self.authenticatedAdminUser, is_membership_on_request=False)
        self.group.join(self.authenticatedUser, 'member')

        self.pad = FileFolder.objects.create(
            type=FileFolder.Types.PAD,
            title="Test group pad",
            rich_description="JSON to string",
            group=self.group,
            read_access=[ACCESS_TYPE.group.format(self.group.id)],
            write_access=[ACCESS_TYPE.group.format(self.group.id)],
            owner=self.authenticatedAdminUser
        )

    def tearDown(self):
        self.pad.delete()
        self.authenticatedUser.delete()
        self.authenticatedAdminUser.delete()
        self.authenticatedNotGroupMember.delete()
        super().tearDown()

    def test_pad_owner(self):
        query = """
            fragment PadParts on Pad {
                title
                richDescription
                accessId
                timeCreated
                timeUpdated
                canEdit
                url
                group {
                    guid
                }
                downloadAsOptions {
                    type
                    url
                }
            }
            query GetPad($guid: String!) {
                entity(guid: $guid) {
                    guid
                    status
                    ...PadParts
                    __typename
                }
            }
        """

        variables = {
            "guid": self.pad.guid
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(query, variables)

        entity = result["data"]["entity"]

        self.assertEqual(entity["guid"], self.pad.guid)
        self.assertEqual(entity["title"], self.pad.title)
        self.assertEqual(entity["richDescription"], self.pad.rich_description)
        self.assertEqual(entity["accessId"], 4)
        self.assertEqual(entity["group"]["guid"], self.group.guid)
        self.assertEqual(entity["timeCreated"], self.pad.created_at.isoformat())
        self.assertEqual(entity["canEdit"], True)
        self.assertEqual(entity["url"], "/files/view/{}/{}".format(self.pad.guid, slugify(self.pad.title)))
        self.assertEqual(entity["downloadAsOptions"], [
            {"type": "odt", "url": "/download_rich_description_as/{}/{}".format(self.pad.guid, "odt") },
            {"type": "html", "url": "/download_rich_description_as/{}/{}".format(self.pad.guid, "html") },
        ])


    def test_pad_non_group_member(self):
        query = """
            fragment PadParts on Pad {
                title
                richDescription
                accessId
                timeCreated
                timeUpdated
                canEdit
                url
                group {
                    guid
                }
            }
            query GetPad($guid: String!) {
                entity(guid: $guid) {
                    guid
                    status
                    ...PadParts
                }
            }
        """

        variables = {
            "guid": self.pad.guid
        }

        self.graphql_client.force_login(self.authenticatedNotGroupMember)
        result = self.graphql_client.post(query, variables)

        entity = result["data"]["entity"]
        self.assertIsNone(entity)
