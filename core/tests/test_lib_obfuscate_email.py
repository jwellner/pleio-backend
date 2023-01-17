from core.lib import obfuscate_email
from core.tests.helpers import PleioTenantTestCase


class TestLibObfuscateEmailTestCase(PleioTenantTestCase):

    def test_email_address(self):
        self.assertEqual(obfuscate_email("0123@example.com"), "0***@example.com")
        self.assertEqual(obfuscate_email("0123456789@example.com"), "0*********@example.com")

    def test_not_a_valid_email_address(self):
        self.assertEqual(obfuscate_email(100), "")
        self.assertEqual(obfuscate_email("not-a-valid-email-address"), "")
