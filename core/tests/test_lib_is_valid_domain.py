from unittest import mock

from core.lib import is_valid_domain
from core.tests.helpers import PleioTenantTestCase


class TestLibIsvalidDomain(PleioTenantTestCase):

    def test_valid_domain(self):
        self.assertTrue(is_valid_domain("foo.com"))
        self.assertFalse(is_valid_domain("foo.com/subpage"))
        self.assertFalse(is_valid_domain("fóô.com"))

    @mock.patch("core.lib.re.compile")
    def test_valid_domain_exception(self, match):
        matcher = mock.MagicMock()
        matcher.match.side_effect = AttributeError()
        match.return_value = matcher

        self.assertFalse(is_valid_domain("foo.com"))
