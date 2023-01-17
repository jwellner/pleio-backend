from http import HTTPStatus

from control.tests.helpers import Control as _


class TestViewAgreementsTestCase(_.BaseTestCase):

    def test_anonymous_visitor(self):
        response = self.client.get(_.reverse("agreements"))

        self.assertNotEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateNotUsed(response, "agreements.html")

    def test_list_agreements(self):
        self.client.force_login(self.admin)
        response = self.client.get(_.reverse("agreements"))

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "agreements.html")
