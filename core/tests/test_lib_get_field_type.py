from core.lib import get_field_type
from core.tests.helpers import PleioTenantTestCase


class TestLibGetFieldTypeTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.expected_field_types = {
            "select_field": "selectField",
            "date_field": "dateField",
            "html_field": "htmlField",
            "multi_select_field": "multiSelectField",
            "text_field": "textField",
            "unknown_field": "textField",
        }

    def test_get_field_type(self):
        for field_type, expected_translation in self.expected_field_types.items():
            self.assertEqual(get_field_type(field_type), expected_translation)
