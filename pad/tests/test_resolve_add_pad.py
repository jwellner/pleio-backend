from django.utils import timezone
from backend2.schema import schema
from ariadne import graphql_sync
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from mixer.backend.django import mixer


class AddPadTestCase(PleioTenantTestCase):

    def setUp(self):
        super(AddPadTestCase, self).setUp()
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)
        self.authenticatedUserNonGroupMember = mixer.blend(User)
        self.adminUser = mixer.blend(User, roles=['ADMIN'])
        self.group = mixer.blend(Group, owner=self.authenticatedUser, is_membership_on_request=False)
        self.group.join(self.authenticatedUser, 'owner')

        self.data = {
            "input": {
                "containerGuid": str(self.group.id),
                "title": "My first Pad",
                "richDescription": "richDescription",
            }
        }
        self.mutation = """
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
            mutation ($input: addPadInput!) {
                addPad(input: $input) {
                    entity {
                    guid
                    status
                    ...PadParts
                    }
                }
            }
        """

    def test_add_pad(self):

        variables = self.data

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result["data"]['addPad']['entity']

        self.assertEqual(entity["title"], variables["input"]["title"])
        self.assertEqual(entity["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(entity["accessId"], 4)
        self.assertEqual(entity["group"]["guid"], self.group.guid)
