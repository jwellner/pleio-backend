import json

from django.core.files import File
from django.conf import settings
from core.models import Group
from core.constances import USER_NOT_MEMBER_OF_GROUP
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from file.models import FileFolder
from core.constances import ACCESS_TYPE
from mixer.backend.django import mixer
from unittest.mock import MagicMock, patch


class AddFileTestCase(PleioTenantTestCase):

    def setUp(self):
        super(AddFileTestCase, self).setUp()

        self.authenticatedUser = mixer.blend(User)
        self.mutation = """
            mutation ($input: addEntityInput!) {
                addEntity(input: $input) {
                    entity {
                        guid
                        status
                        ... on File {
                            title
                            description
                            richDescription
                            timeCreated
                            timeUpdated
                            accessId
                            writeAccessId
                            canEdit
                            tags
                            url
                            inGroup
                            group {
                                guid
                            }
                            mimeType
                        }
                        ... on Folder {
                            title
                            description
                            richDescription
                            timeCreated
                            timeUpdated
                            accessId
                            writeAccessId
                            canEdit
                            tags
                            url
                            inGroup
                            group {
                                guid
                            }
                        }
                    }
                }
            }
        """

    def test_add_minimal_folder(self):
        variables = {
            'input': {
                'title': "Simple folder",
                'subtype': "folder",
            }
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result["data"]["addEntity"]["entity"]
        self.assertTrue(entity['canEdit'])
