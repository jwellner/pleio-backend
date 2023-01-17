from http import HTTPStatus

from control.tests.helpers import Control as _


class TestViewAddAgreementTestCase(_.BaseTestCase):

    def test_anonymous_visitor(self):
        response = self.client.get(_.reverse("agreement_add"))
        self.assertNotEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateNotUsed("agreements_add.html")

    def test_add_agreement(self):
        self.client.force_login(self.admin)
        response = self.client.get(_.reverse("agreement_add"))

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed("agreements_add.html")

    def test_add_agreement_submit(self):
        from tenants.models import Agreement
        self.client.force_login(self.admin)
        response = self.client.post(_.reverse("agreement_add"), data={
            "name": "Demo"
        })

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, _.reverse("agreements"))
        self.assertTrue(Agreement.objects.filter(name="Demo").exists())
