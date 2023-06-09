from django.contrib.auth.models import AnonymousUser
from core.models import Group
from file.models import FileFolder
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from core.constances import ACCESS_TYPE
from mixer.backend.django import mixer


class EditPadTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)
        self.authenticatedUserNonGroupMember = mixer.blend(User)
        self.adminUser = mixer.blend(User, roles=['ADMIN'])
        self.group = mixer.blend(Group, owner=self.authenticatedUser, is_membership_on_request=False, is_closed=True)
        self.group.join(self.authenticatedUser, 'owner')

        self.pad = FileFolder.objects.create(
            type=FileFolder.Types.PAD,
            title="Test group pad",
            rich_description="JSON to string",
            group=self.group,
            read_access=[ACCESS_TYPE.group.format(self.group.id)],
            write_access=[ACCESS_TYPE.group.format(self.group.id)],
            owner=self.authenticatedUser
        )

        self.data = {
            "input": {
                "guid": str(self.pad.id),
                "title": "My first Pad",
                "richDescription": "richDescription",
                "accessId": 0,
                "writeAccessId": 0
            }
        }
        self.mutation = """
            fragment PadParts on Pad {
                title
                richDescription
                accessId
                writeAccessId
                timeCreated
                timeUpdated
                canEdit
                url
                group {
                    guid
                }
            }
            mutation ($input: editPadInput!) {
                editPad(input: $input) {
                    entity {
                    guid
                    status
                    ...PadParts
                    }
                }
            }
        """

    def test_edit_pad(self):

        variables = self.data

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result["data"]['editPad']['entity']

        self.assertEqual(entity["title"], variables["input"]["title"])
        self.assertEqual(entity["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(entity["accessId"], 0)
        self.assertEqual(entity["writeAccessId"], 0)
        self.assertEqual(entity["group"]["guid"], self.group.guid)
        self.assertEqual(entity["group"]["guid"], self.group.guid)