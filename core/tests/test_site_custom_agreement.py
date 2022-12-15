from core.tests.helpers import PleioTenantTestCase
from mixer.backend.django import mixer
from user.factories import UserFactory, AdminFactory
from core.models import CustomAgreement


class CustomSiteAgreementTestCase(PleioTenantTestCase):

    def setUp(self):
        super(CustomSiteAgreementTestCase, self).setUp()
        
        self.user = UserFactory()
        self.admin = AdminFactory()
        self.agreement = mixer.blend(CustomAgreement,
            document=self.build_contentfile(self.relative_path(__file__, ['assets', 'text_file.txt'])))

    def test_site_custom_agreement_not_logged_in(self):
        response = self.client.get("/custom_agreement/{}".format(self.agreement.id))
        self.assertEqual(response.status_code, 401)
        self.assertFalse(hasattr(response, 'streaming_content'))

    def test_site_custom_agreement_not_admin(self):
        self.client.force_login(self.user)
        response = self.client.get("/custom_agreement/{}".format(self.agreement.id))
        self.assertFalse(hasattr(response, 'streaming_content'))

    def test_site_custom_agreement(self):
        self.client.force_login(self.admin)
        response = self.client.get("/custom_agreement/{}".format(self.agreement.id))
        self.assertEqual(response.headers['Content-Type'], 'application/pdf')
        self.assertTrue(list(response.streaming_content), "Demo upload file.")