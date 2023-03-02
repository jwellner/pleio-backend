from unittest import mock

from core.tests.helpers import PleioTenantTestCase
from core.utils.clamav import FileScanError, FILE_SCAN
from file.factories import FileFactory
from file.tasks import scan_file
from user.factories import UserFactory


class TestTaskScanFileTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.owner = UserFactory()
        self.file = FileFactory(owner=self.owner,
                                upload=self.build_contentfile(self.relative_path(__file__, ['assets', 'navy.jpg'])))
        self.scan = mock.patch("core.utils.clamav.scan").start()
        self.create_incident = mock.patch('file.models.ScanIncidentManager.create_from_file_folder').start()

    def tearDown(self):
        self.file.delete()
        self.owner.delete()
        super().tearDown()

    def test_scan_file_without_virus(self):
        scan_file(self.tenant.schema_name, self.file.guid)
        self.file.refresh_from_db()

        self.assertIsNotNone(self.file.last_scan)
        self.assertTrue(self.scan.called)
        self.assertFalse(self.create_incident.called)

    def test_scan_file_with_virus(self):
        self.scan.side_effect = FileScanError(FILE_SCAN.VIRUS, "NL.SARS.PLEIO.665G")

        scan_file(self.tenant.schema_name, self.file.guid)
        self.file.refresh_from_db()

        self.assertTrue(self.file.blocked)
        self.assertTrue(self.create_incident.called)

    def test_scan_file_with_another_error(self):
        self.scan.side_effect = FileScanError(FILE_SCAN.UNKNOWN, "Not a clue on what happened")

        scan_file(self.tenant.schema_name, self.file.guid)
        self.file.refresh_from_db()

        self.assertFalse(self.file.blocked)
        self.assertTrue(self.create_incident.called)
