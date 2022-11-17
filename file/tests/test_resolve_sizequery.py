from django.utils import timezone
from mixer.backend.django import mixer

from core.constances import ACCESS_TYPE
from core.tests.helpers import PleioTenantTestCase
from file.models import FileFolder
from user.models import User


class TestResolveSizeQueryTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.authenticatedUser = mixer.blend(User)

        self.file1 = mixer.blend(FileFolder, title="File1", size=80, type=FileFolder.Types.FILE,
                                 time_created=timezone.now() - timezone.timedelta(days=6),
                                 owner=self.authenticatedUser,
                                 read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)])
        self.file2 = mixer.blend(FileFolder, title="File2", size=40, type=FileFolder.Types.FILE,
                                 time_created=timezone.now() - timezone.timedelta(days=8),
                                 owner=self.authenticatedUser,
                                 read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)])
        self.file3 = mixer.blend(FileFolder, title="File3", size=20, type=FileFolder.Types.FILE,
                                 time_created=timezone.now() - timezone.timedelta(days=10),
                                 owner=self.authenticatedUser,
                                 read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)])

        self.folder1 = mixer.blend(FileFolder, title="Folder1", type=FileFolder.Types.FOLDER,
                                   owner=self.authenticatedUser,
                                   read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)])

        self.file4 = mixer.blend(FileFolder, title="File4", size=60, type=FileFolder.Types.FILE, parent=self.folder1,
                                 time_created=timezone.now() - timezone.timedelta(days=4),
                                 owner=self.authenticatedUser,
                                 read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)])
        self.file5 = mixer.blend(FileFolder, title="File5", size=100, type=FileFolder.Types.FILE, parent=self.folder1,
                                 time_created=timezone.now() - timezone.timedelta(days=2),
                                 owner=self.authenticatedUser,
                                 read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)])

        self.query = """
        query FileSummary(
                  $typeFilter: [String]
                  $orderBy: String
                  $dir: String) {
            files(typeFilter: $typeFilter, orderBy: $orderBy, orderDirection: $dir) {
                edges {
                   ... on File {
                       title
                       parentFolder {
                         title
                       }
                   }
                   ... on Folder {
                       title
                       parentFolder {
                         title
                       }
                   }
                }
            }
        }
        """

    def test_order_by_size(self):
        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.query, {
            'typeFilter': ['file'],
            'orderBy': 'size',
            'dir': 'asc',
        })

        self.assertEqual([r['title'] for r in result['data']['files']['edges']],
                         ["File3", "File2", "File4", "File1", "File5", ])

    def test_order_by_size_desc(self):
        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.query, {
            'typeFilter': ['file'],
            'orderBy': 'size',
            'dir': 'desc'
        })

        self.assertEqual([r['title'] for r in result['data']['files']['edges']],
                         ["File5", "File1", "File4", "File2", "File3", ])
