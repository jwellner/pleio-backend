from http import HTTPStatus

from core.tests.helpers import PleioTenantTestCase
from mixer.backend.django import mixer
from user.factories import UserFactory, AdminFactory
from core.models import CustomAgreement


class CustomSiteAgreementTestCase(PleioTenantTestCase):

    def setUp(self):
        super(CustomSiteAgreementTestCase, self).setUp()

        self.user = UserFactory()
        self.admin = AdminFactory()
        self.agreement_file_path = self.relative_path(__file__, ['assets', 'text_file.txt'])
        self.agreement = mixer.blend(CustomAgreement,
                                     document=self.build_contentfile(self.agreement_file_path))
        with open(self.agreement_file_path, 'rb') as fh:
            self.expected_content = fh.read()

    def test_site_custom_agreement_not_logged_in(self):
        self.override_config(IS_CLOSED=False)
        response = self.client.get("/custom_agreement/{}".format(self.agreement.id))
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)
        self.assertTemplateUsed("react.html")
        self.assertFalse(hasattr(response, 'streaming_content'))

    def test_site_custom_agreement_not_admin(self):
        self.client.force_login(self.user)
        response = self.client.get("/custom_agreement/{}".format(self.agreement.id))

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertFalse(hasattr(response, 'streaming_content'))
        self.assertTemplateUsed("react.html")

    def test_site_custom_agreement(self):
        self.client.force_login(self.admin)

        response = self.client.get("/custom_agreement/{}".format(self.agreement.id))
        content = response.getvalue()

        self.assertEqual(response.headers['Content-Type'], 'application/pdf')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn(self.expected_content, content)

    def test_site_non_existing_agreement(self):
        self.client.force_login(self.admin)

        response = self.client.get("/custom_agreement/{}".format(self.agreement.id + 1000))
        content = response.getvalue()

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertNotIn(self.expected_content, content)
        self.assertTemplateUsed("react.html")
