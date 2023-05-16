from datetime import timedelta
from django.utils import timezone
from core.models import Group, GroupInvitation, Entity
from core.models.tags import Tag, TagSynonym
from core.tests.helpers import PleioTenantTestCase
from tenants.helpers import FastTenantTestCase
from user.models import User
from file.models import FileFolder
from core.constances import ACCESS_TYPE
from mixer.backend.django import mixer


class EntityTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.authenticatedUser = mixer.blend(User)
        self.user1 = mixer.blend(User)
        self.group = mixer.blend(Group, owner=self.authenticatedUser)
        self.folder = FileFolder.objects.create(
            owner=self.authenticatedUser,
            upload=None,
            type=FileFolder.Types.FOLDER,
            parent=None,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)]
        )
        self.subFolder = FileFolder.objects.create(
            owner=self.authenticatedUser,
            upload=None,
            type=FileFolder.Types.FOLDER,
            parent=self.folder,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)]
        )
        self.file = FileFolder.objects.create(
            owner=self.authenticatedUser,
            upload=None,
            type=FileFolder.Types.FILE,
            parent=self.subFolder,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)]
        )
        self.invitation = GroupInvitation.objects.create(code="7d97cea90c83722c7262", invited_user=self.user1,
                                                         group=self.group)

    def tearDown(self):
        super().tearDown()

    def test_entity_user_anonymous(self):
        query = """
            query getUser($username: String!) {
                entity(username: $username) {
                    guid
                    status
                    ... on User {
                        email
                    }
                    __typename
                }
            }
        """

        variables = {
            "username": self.authenticatedUser.guid
        }

        result = self.graphql_client.post(query, variables)

        data = result["data"]
        self.assertEqual(data["entity"]["guid"], self.authenticatedUser.guid)
        self.assertEqual(data["entity"]["email"], None)
        self.assertEqual(data["entity"]["__typename"], "User")

    def test_entity_user_by_username(self):
        query = """
            query getUser($username: String!) {
                entity(username: $username) {
                    guid
                    status
                    ... on User {
                        email
                    }
                    __typename
                }
            }
        """
        variables = {
            "username": self.authenticatedUser.guid
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(query, variables)

        data = result["data"]
        self.assertEqual(data["entity"]["guid"], self.authenticatedUser.guid)
        self.assertEqual(data["entity"]["email"], self.authenticatedUser.email)
        self.assertEqual(data["entity"]["__typename"], "User")

    def test_entity_user_by_guid(self):
        query = """
            query getUser($guid: String!) {
                entity(guid: $guid) {
                    guid
                    status
                    __typename
                }
            }
        """
        variables = {
            "guid": self.authenticatedUser.guid
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(query, variables)

        data = result["data"]
        self.assertEqual(data["entity"]["guid"], self.authenticatedUser.guid)
        self.assertEqual(data["entity"]["__typename"], "User")

    def test_entity_group(self):
        query = """
            query getGroup($guid: String!) {
                entity(guid: $guid) {
                    guid
                    status
                    __typename
                }
            }
        """

        variables = {
            "guid": self.group.guid
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(query, variables)

        data = result["data"]
        self.assertEqual(data["entity"]["guid"], self.group.guid)
        self.assertEqual(data["entity"]["__typename"], "Group")

    def test_entity_file_folder(self):
        query = """
            query getFileFolder($guid: String!) {
                entity(guid: $guid) {
                    guid
                    status
                    __typename
                }
            }
        """
        variables = {
            "guid": self.file.guid
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(query, variables)

        data = result["data"]
        self.assertEqual(data["entity"]["guid"], self.file.guid)
        self.assertEqual(data["entity"]["__typename"], "File")

    def test_entity_archived(self):
        query = """
            query getFileFolder($guid: String!) {
                entity(guid: $guid) {
                    guid
                }
            }
        """
        self.file.is_archived = True
        self.file.save()
        variables = {
            "guid": self.file.guid
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(query, variables)

        data = result["data"]
        self.assertEqual(data["entity"]["guid"], self.file.guid)

    def test_entity_breadcrumb_file_folder(self):
        query = """
            query Breadcrumb($guid: String!) {
                breadcrumb(guid: $guid) {
                    ... on File {
                        guid
                        title
                        __typename
                    }
                    ... on Folder {
                        guid
                        title
                        __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "guid": self.file.guid
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(query, variables)

        data = result["data"]
        self.assertEqual(data["breadcrumb"][0]["guid"], self.folder.guid)
        self.assertEqual(data["breadcrumb"][1]["guid"], self.subFolder.guid)


class EntityModelTestCase(FastTenantTestCase):

    def test_published_status(self):
        tests = [
            (False, None, 'draft'),
            (False, timezone.now() + timedelta(days=1), 'draft'),
            (False, timezone.now() + timedelta(days=-1), 'published'),
            (True, None, 'archived'),
            (True, timezone.now() + timedelta(days=-1), 'archived'),
        ]

        for is_archived, published, expected in tests:
            with self.subTest(is_archived=is_archived, published=published):
                entity = mixer.blend(
                    Entity,
                    is_archived=is_archived,
                    published=published)

                result = entity.status_published

                self.assertEqual(result, expected)


class TagModelTestCase(FastTenantTestCase):

    def test_tag_translation_table(self):
        tag1 = Tag.objects.create(label='tag1')
        Tag.objects.create(label='tag2')
        Tag.objects.create(label='tag3')
        TagSynonym.objects.create(label='tag1.1', tag=tag1)
        TagSynonym.objects.create(label='tag1.2', tag=tag1)
        TagSynonym.objects.create(label='tag1.3', tag=tag1)

        input_tags = ['tag1.1', 'tag2', 'tag4']
        self.assertEqual([t for t in Tag.translate_tags(input_tags)], ['tag1', 'tag2', 'tag4'])
