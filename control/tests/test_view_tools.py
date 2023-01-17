from http import HTTPStatus

from control.tests.helpers import Control as _


class TestViewToolsTestCase(_.BaseTestCase):

    def test_anonymous_visitor(self):
        response = self.client.get(_.reverse('tools'))

        self.assertNotEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateNotUsed(response, "tools.html")

    def test_view_tools(self):
        self.client.force_login(self.admin)
        response = self.client.get(_.reverse('tools'))

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "tools.html")
