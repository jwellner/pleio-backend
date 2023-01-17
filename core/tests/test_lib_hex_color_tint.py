from unittest import mock

from core.lib import hex_color_tint
from core.tests.helpers import PleioTenantTestCase


class TestLibHexColorTintTestCase(PleioTenantTestCase):

    def test_hex_color_tint(self):
        self.assertEqual(hex_color_tint("#010203"), "#808081")
        self.assertEqual(hex_color_tint("#010203", .75), "#bfc0c0")

        with mock.patch("core.lib.Color") as color:
            color.side_effect = AttributeError()
            self.assertEqual(hex_color_tint("#010203"), "#010203")
