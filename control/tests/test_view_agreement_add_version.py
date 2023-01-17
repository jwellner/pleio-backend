from http import HTTPStatus

from django.core.files.uploadedfile import SimpleUploadedFile
from mixer.backend.django import mixer

from control.tests.helpers import Control as _


class TestViewAddAgreementVersionTestCase(_.BaseTestCase):

    def setUp(self):
        super().setUp()

        from tenants.models import Agreement
        self.agreement = mixer.blend(Agreement)

    def tearDown(self):
        self.agreement.delete()

        super().tearDown()

    def test_anonymous_visitor(self):
        response = self.client.get(_.reverse("agreement_add_version", args=[self.agreement.id]))

        self.assertNotEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateNotUsed(response, "agreements_add.html")

    def test_add_agreement_version(self):
        self.client.force_login(self.admin)
        response = self.client.get(_.reverse("agreement_add_version", args=[self.agreement.id]))

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "agreements_add.html")

    def test_add_version_to_not_existing_agreement(self):
        from tenants.models import Agreement
        another_agreement = mixer.blend(Agreement)
        another_agreement_id = another_agreement.id
        another_agreement.delete()

        self.client.force_login(self.admin)
        response = self.client.get(_.reverse("agreement_add_version", args=[another_agreement_id]))

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateNotUsed(response, "agreements_add.html")

    def test_add_agreement_version_submit(self):
        self.client.force_login(self.admin)
        response = self.client.post(_.reverse("agreement_add_version", args=[self.agreement.id]), data={
            "agreement_id": self.agreement.id,
            "version": "Demo version",
            "document": SimpleUploadedFile("agreement.txt", b"Demo content\n", content_type="text/plain")
        })

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, _.reverse("agreements"))

        new_version = self.agreement.versions.first()
        self.assertTrue(bool(new_version))
        self.assertEqual(new_version.version, "Demo version")
        self.assertEqual(new_version.document.open().read(), b"Demo content\n")
