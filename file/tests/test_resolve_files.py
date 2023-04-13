from core.factories import GroupFactory
from core.models import Group, Subgroup
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from file.models import FileFolder
from mixer.backend.django import mixer
from core.constances import ACCESS_TYPE


class TestFileQueryOrderByAccessWeight(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.owner = mixer.blend(User)
        self.group = GroupFactory(owner=self.owner)
        self.subgroup = mixer.blend(Subgroup, group=self.group, members=[self.owner])

        self.public_file = mixer.blend(FileFolder,
                                       read_access=[ACCESS_TYPE.public],
                                       write_access=[ACCESS_TYPE.public],
                                       group=self.group,
                                       title="public")
        self.authentic_file = mixer.blend(FileFolder,
                                          read_access=[ACCESS_TYPE.logged_in],
                                          write_access=[ACCESS_TYPE.logged_in],
                                          group=self.group,
                                          title="logged_in")
        self.subgroup_file = mixer.blend(FileFolder,
                                         read_access=[ACCESS_TYPE.subgroup.format(self.subgroup.access_id)],
                                         write_access=[ACCESS_TYPE.subgroup.format(self.subgroup.access_id)],
                                         group=self.group,
                                         title="subgroup")
        self.group_file = mixer.blend(FileFolder,
                                      read_access=[ACCESS_TYPE.group.format(self.group.id)],
                                      write_access=[ACCESS_TYPE.group.format(self.group.id)],
                                      group=self.group,
                                      title="group")
        self.user_file = mixer.blend(FileFolder,
                                     read_access=[ACCESS_TYPE.user.format(self.owner.id)],
                                     write_access=[ACCESS_TYPE.user.format(self.owner.id)],
                                     group=self.group,
                                     title="private")
        self.query = """
            query FilesQuery($containerGuid: String!, $orderBy: String, $orderDirection: String) {
                files(containerGuid: $containerGuid, orderBy: $orderBy, orderDirection: $orderDirection) {
                    total
                    edges {
                        guid
                    }
                }
            }
        """

    def test_read_access_weight_of_files(self):
        variables = {
            "containerGuid": self.group.guid,
            "orderBy": "readAccessWeight",
        }

        self.graphql_client.force_login(self.owner)
        result = self.graphql_client.post(self.query, variables)

        actual_order = [record['guid'] for record in result['data']['files']['edges']]
        self.assertEqual(actual_order, [
            self.user_file.guid,
            self.subgroup_file.guid,
            self.group_file.guid,
            self.authentic_file.guid,
            self.public_file.guid,
        ])

    def test_read_access_weight_of_files_reverse(self):
        variables = {
            "containerGuid": self.group.guid,
            "orderBy": "readAccessWeight",
            "orderDirection": "desc"
        }

        self.graphql_client.force_login(self.owner)
        result = self.graphql_client.post(self.query, variables)

        actual_order = [record['guid'] for record in result['data']['files']['edges']]
        self.assertEqual(actual_order, [
            self.public_file.guid,
            self.authentic_file.guid,
            self.group_file.guid,
            self.subgroup_file.guid,
            self.user_file.guid,
        ])

    def test_write_access_weight_of_files(self):
        variables = {
            "containerGuid": self.group.guid,
            "orderBy": "writeAccessWeight",
        }

        self.graphql_client.force_login(self.owner)
        result = self.graphql_client.post(self.query, variables)

        actual_order = [record['guid'] for record in result['data']['files']['edges']]
        self.assertEqual(actual_order, [
            self.user_file.guid,
            self.subgroup_file.guid,
            self.group_file.guid,
            self.authentic_file.guid,
            self.public_file.guid,
        ])

    def test_write_access_weight_of_files_reverse(self):
        variables = {
            "containerGuid": self.group.guid,
            "orderBy": "writeAccessWeight",
            "orderDirection": "desc"
        }

        self.graphql_client.force_login(self.owner)
        result = self.graphql_client.post(self.query, variables)

        actual_order = [record['guid'] for record in result['data']['files']['edges']]
        self.assertEqual(actual_order, [
            self.public_file.guid,
            self.authentic_file.guid,
            self.group_file.guid,
            self.subgroup_file.guid,
            self.user_file.guid,
        ])


class FilesTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.authenticatedUser = mixer.blend(User)

        self.group = mixer.blend(Group, owner=self.authenticatedUser)

        self.folder = FileFolder.objects.create(
            title="images",
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            type=FileFolder.Types.FOLDER
        )

        self.file1 = FileFolder.objects.create(
            owner=self.authenticatedUser,
            upload=None,
            title="file1",
            type=FileFolder.Types.FILE,
            group=None,
            parent=None,
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)]
        )
        self.file2 = FileFolder.objects.create(
            owner=self.authenticatedUser,
            upload=None,
            title="file2",
            type=FileFolder.Types.FILE,
            group=None,
            parent=self.folder,
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)]
        )

        self.file3 = FileFolder.objects.create(
            owner=self.authenticatedUser,
            upload=None,
            title="file3",
            type=FileFolder.Types.FILE,
            group=self.group,
            parent=None,
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)]
        )

        self.query = """
            query FilesQuery($containerGuid: String!) {
                files(containerGuid: $containerGuid) {
                    total
                    edges {
                        guid
                        ... on File {
                            title
                        }
                        ... on Folder {
                            title
                        }
                    }
                }
            }
        """

    def tearDown(self):
        FileFolder.objects.all().delete()
        self.authenticatedUser.delete()
        super().tearDown()

    def test_user_container(self):
        variables = {
            "containerGuid": self.authenticatedUser.guid
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.query, variables)

        data = result['data']
        self.assertEqual(data["files"]["total"], 2)
        self.assertEqual(data["files"]["edges"][0]["title"], "images")
        self.assertEqual(data["files"]["edges"][1]["title"], "file1")

    def test_folder_container(self):
        variables = {
            "containerGuid": self.folder.guid
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.query, variables)

        data = result['data']
        self.assertEqual(data["files"]["total"], 1)
        self.assertEqual(data["files"]["edges"][0]["title"], "file2")

    def test_group_container(self):
        variables = {
            "containerGuid": self.group.guid
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.query, variables)

        data = result['data']
        self.assertEqual(data["files"]["total"], 1)
        self.assertEqual(data["files"]["edges"][0]["title"], "file3")
