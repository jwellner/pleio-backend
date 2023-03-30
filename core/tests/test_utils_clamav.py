from unittest import mock

import clamd

from core.tests.helpers import PleioTenantTestCase
from core.utils import clamav
from core.utils.clamav import FILE_SCAN


class TestUtilsClamavTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.override_setting(CLAMAV_HOST='clamav')

        self.clamav_connection = mock.MagicMock()
        self.file_path = self.relative_path(__file__, ['assets', 'landscape.jpeg'])

        self.clamav_socket = mock.patch('core.utils.clamav.clamd.ClamdNetworkSocket').start()
        self.clamav_socket.return_value = self.clamav_connection

    def test_scan_disabled(self):
        self.override_setting(CLAMAV_HOST=None)

        response = clamav.scan(self.file_path)

        self.assertEqual(response, FILE_SCAN.CLEAN)
        self.assertFalse(self.clamav_socket.called)

    def test_scan_enabled(self):
        response = clamav.scan(self.file_path)

        self.assertEqual(response, FILE_SCAN.CLEAN)
        self.assertTrue(self.clamav_socket.called)
        self.assertTrue(self.clamav_connection.instream.called)

    @mock.patch('os.path.exists')
    def test_scan_unexisting_file(self, mocked_exists):
        mocked_exists.return_value = False

        try:
            clamav.scan(self.file_path)
            self.fail("Unexpectedly scanned non-existing file")  # pragma: no cover
        except clamav.FileScanError as e:
            self.assertFalse(self.clamav_socket.called)
            self.assertFalse(self.clamav_connection.instream.called)
            self.assertEqual(e.status, FILE_SCAN.NOTFOUND)

    def test_scan_with_virus(self):
        EXPECTED_FEEDBACK = "NL.SARS.PLEIO.Z665"
        self.clamav_connection.instream.return_value = {
            "stream": ['FOUND', EXPECTED_FEEDBACK]
        }

        try:
            clamav.scan(self.file_path)
            self.fail("Unexpecedly did not recognize clamav virus found behaviour")  # pragma: no cover
        except clamav.FileScanError as e:
            self.assertTrue(self.clamav_socket.called)
            self.assertTrue(self.clamav_connection.instream.called)
            self.assertEqual(e.status, FILE_SCAN.VIRUS)
            self.assertEqual(e.feedback, EXPECTED_FEEDBACK)

    def test_scan_with_connection_error(self):
        self.clamav_socket.side_effect = clamd.ConnectionError()

        try:
            clamav.scan(self.file_path)
            self.fail("Unexpecedly did not recognize clamav virus found behaviour")  # pragma: no cover
        except clamav.FileScanError as e:
            self.assertTrue(self.clamav_socket.called)
            self.assertFalse(self.clamav_connection.instream.called)
            self.assertEqual(e.status, FILE_SCAN.OFFLINE)

    def test_scan_with_unexpected_error(self):
        class UnexpectedError(Exception):
            pass

        self.clamav_connection.instream.side_effect = UnexpectedError("You did not see this one coming!")

        try:
            clamav.scan(self.file_path)
            self.fail("Unexpecedly did not recognize unexpected error behaviour")  # pragma: no cover
        except clamav.FileScanError as e:
            self.assertTrue(self.clamav_socket.called)
            self.assertTrue(self.clamav_connection.instream.called)
            self.assertEqual(e.status, FILE_SCAN.UNKNOWN)

    def test_skip_av_negative(self):
        self.assertFalse(clamav.skip_av())

    def test_skip_av_positive(self):
        self.override_setting(CLAMAV_HOST=None)

        self.assertTrue(clamav.skip_av())
