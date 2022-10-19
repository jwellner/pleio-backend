from core.models import Group
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from core.constances import ACCESS_TYPE
from mixer.backend.django import mixer
from ..models import FileFolder


class MoveFileFolderTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.authenticatedUser = mixer.blend(User)

        self.group = mixer.blend(Group, owner=self.authenticatedUser, is_membership_on_request=False)
        self.group.join(self.authenticatedUser, 'owner')

        self.folder_root = FileFolder.objects.create(
            title="root",
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            type=FileFolder.Types.FOLDER,
        )

        self.folder = FileFolder.objects.create(
            title="images",
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            type=FileFolder.Types.FOLDER,
            parent=self.folder_root
        )

        self.file = FileFolder.objects.create(
            title="file.jpg",
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
        )

        self.data = {
            "input": {
                "guid": None,
                "containerGuid": None,
            }
        }
        self.mutation = """
            mutation ($input: moveFileFolderInput!) {
                moveFileFolder(input: $input) {
                    entity {
                        guid
                        status
                        ... on File {
                            title
                            parentFolder {
                                guid
                            }
                            group {
                                guid
                            }
                        }
                        ... on Folder {
                            title
                            parentFolder {
                                guid
                            }
                            group {
                                guid
                            }
                        }
                    }
                }
            }
        """

    def test_move_file_to_folder(self):
        variables = self.data

        variables["input"]["guid"] = self.file.guid
        variables["input"]["containerGuid"] = self.folder.guid

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, variables)

        data = result['data']
        self.assertEqual(data["moveFileFolder"]["entity"]["parentFolder"]["guid"], self.folder.guid)

    def test_move_file_to_group(self):
        variables = self.data

        variables["input"]["guid"] = self.file.guid
        variables["input"]["containerGuid"] = self.group.guid

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, variables)

        data = result['data']
        self.assertEqual(data["moveFileFolder"]["entity"]["parentFolder"], None)
        self.assertEqual(data["moveFileFolder"]["entity"]["group"]["guid"], self.group.guid)

    def test_move_folder_to_group(self):
        variables = self.data

        variables["input"]["guid"] = self.folder.guid
        variables["input"]["containerGuid"] = self.group.guid

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, variables)

        data = result['data']
        self.assertEqual(data["moveFileFolder"]["entity"]["parentFolder"], None)
        self.assertEqual(data["moveFileFolder"]["entity"]["group"]["guid"], self.group.guid)

    def test_move_folder_to_self(self):
        variables = self.data

        variables["input"]["guid"] = self.folder.guid
        variables["input"]["containerGuid"] = self.folder.guid

        with self.assertGraphQlError("INVALID_CONTAINER_GUID"):
            self.graphql_client.force_login(self.authenticatedUser)
            self.graphql_client.post(self.mutation, variables)

    def test_move_folder_to_descendant_folder(self):
        variables = self.data

        variables["input"]["guid"] = self.folder_root.guid
        variables["input"]["containerGuid"] = self.folder.guid

        with self.assertGraphQlError("INVALID_CONTAINER_GUID"):
            self.graphql_client.force_login(self.authenticatedUser)
            self.graphql_client.post(self.mutation, variables)
