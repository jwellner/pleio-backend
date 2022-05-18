from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group, Subgroup
from user.models import User
from file.models import FileFolder
from mixer.backend.django import mixer
from core.constances import ACCESS_TYPE


class TestFileQueryOrderByAccessWeight(FastTenantTestCase):

    def setUp(self):
        self.owner = mixer.blend(User)
        self.group = mixer.blend(Group, owner=self.owner)
        self.group.join(self.owner, 'owner')
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

    def test_read_access_weight_of_files(self):
        request = HttpRequest()
        request.user = self.owner

        query = """
            query FilesQuery($containerGuid: String!, $orderBy: String) {
                files(containerGuid: $containerGuid, orderBy: $orderBy) {
                    total
                    edges {
                        guid
                    }
                }
            }
        """

        variables = {
            "containerGuid": self.group.guid,
            "orderBy": "readAccessWeight",
        }

        success, result = graphql_sync(schema, {"query": query, "variables": variables},
                                       context_value={"request": request})

        actual_order = [record['guid'] for record in result['data']['files']['edges']]
        self.assertEqual(actual_order, [
            self.user_file.guid,
            self.subgroup_file.guid,
            self.group_file.guid,
            self.authentic_file.guid,
            self.public_file.guid,
        ])

    def test_read_access_weight_of_files_reverse(self):
        request = HttpRequest()
        request.user = self.owner

        query = """
            query FilesQuery($containerGuid: String!, $orderBy: String, $orderDirection: String) {
                files(containerGuid: $containerGuid, orderBy: $orderBy, orderDirection: $orderDirection) {
                    total
                    edges {
                        guid
                    }
                }
            }
        """

        variables = {
            "containerGuid": self.group.guid,
            "orderBy": "readAccessWeight",
            "orderDirection": "desc"
        }

        success, result = graphql_sync(schema, {"query": query, "variables": variables},
                                       context_value={"request": request})

        actual_order = [record['guid'] for record in result['data']['files']['edges']]
        self.assertEqual(actual_order, [
            self.public_file.guid,
            self.authentic_file.guid,
            self.group_file.guid,
            self.subgroup_file.guid,
            self.user_file.guid,
        ])

    def test_write_access_weight_of_files(self):
        request = HttpRequest()
        request.user = self.owner

        query = """
            query FilesQuery($containerGuid: String!, $orderBy: String) {
                files(containerGuid: $containerGuid, orderBy: $orderBy) {
                    total
                    edges {
                        guid
                    }
                }
            }
        """

        variables = {
            "containerGuid": self.group.guid,
            "orderBy": "writeAccessWeight",
        }

        success, result = graphql_sync(schema, {"query": query, "variables": variables},
                                       context_value={"request": request})

        actual_order = [record['guid'] for record in result['data']['files']['edges']]
        self.assertEqual(actual_order, [
            self.user_file.guid,
            self.subgroup_file.guid,
            self.group_file.guid,
            self.authentic_file.guid,
            self.public_file.guid,
        ])

    def test_write_access_weight_of_files_reverse(self):
        request = HttpRequest()
        request.user = self.owner

        query = """
            query FilesQuery($containerGuid: String!, $orderBy: String, $orderDirection: String) {
                files(containerGuid: $containerGuid, orderBy: $orderBy, orderDirection: $orderDirection) {
                    total
                    edges {
                        guid
                    }
                }
            }
        """

        variables = {
            "containerGuid": self.group.guid,
            "orderBy": "writeAccessWeight",
            "orderDirection": "desc"
        }

        success, result = graphql_sync(schema, {"query": query, "variables": variables},
                                       context_value={"request": request})

        actual_order = [record['guid'] for record in result['data']['files']['edges']]
        self.assertEqual(actual_order, [
            self.public_file.guid,
            self.authentic_file.guid,
            self.group_file.guid,
            self.subgroup_file.guid,
            self.user_file.guid,
        ])


class FilesCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)

        self.group = mixer.blend(Group, owner=self.authenticatedUser)

        self.folder = FileFolder.objects.create(
            title="images",
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            is_folder=True
        )

        self.file1 = FileFolder.objects.create(
            owner=self.authenticatedUser,
            upload=None,
            title="file1",
            is_folder=False,
            group=None,
            parent=None,
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)]
        )
        self.file2 = FileFolder.objects.create(
            owner=self.authenticatedUser,
            upload=None,
            title="file2",
            is_folder=False,
            group=None,
            parent=self.folder,
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)]
        )

        self.file3 = FileFolder.objects.create(
            owner=self.authenticatedUser,
            upload=None,
            title="file3",
            is_folder=False,
            group=self.group,
            parent=None,
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)]
        )

        self.query = """
            fragment FileParts on FileFolder {
                title
            }
            query FilesQuery($containerGuid: String!) {
                files(containerGuid: $containerGuid) {
                    total
                    edges {
                        guid
                        ...FileParts
                    }
                }
            }
        """

    def tearDown(self):
        FileFolder.objects.all().delete()
        self.authenticatedUser.delete()

    def test_user_container(self):
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {
            "containerGuid": self.authenticatedUser.guid
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={"request": request})

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["files"]["total"], 2)
        self.assertEqual(data["files"]["edges"][0]["title"], "images")
        self.assertEqual(data["files"]["edges"][1]["title"], "file1")

    def test_folder_container(self):
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {
            "containerGuid": self.folder.guid
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={"request": request})

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["files"]["total"], 1)
        self.assertEqual(data["files"]["edges"][0]["title"], "file2")

    def test_group_container(self):
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {
            "containerGuid": self.group.guid
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={"request": request})

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["files"]["total"], 1)
        self.assertEqual(data["files"]["edges"][0]["title"], "file3")
