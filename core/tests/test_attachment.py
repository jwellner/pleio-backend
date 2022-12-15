from core.tests.helpers import PleioTenantTestCase
from core.models import Attachment
from mixer.backend.django import mixer
from user.factories import UserFactory
from core import config


class AttachmentTestCase(PleioTenantTestCase):

    def setUp(self):
        super(AttachmentTestCase, self).setUp()
        config.GROUP_MEMBER_EXPORT = True
        
        self.user1 = UserFactory()
        self.user2 = UserFactory()
        self.attachment = mixer.blend(Attachment, 
            upload=self.build_contentfile(self.relative_path(__file__, ['assets', 'exif_example.jpg'])),
            owner = self.user1)

    def test_attachment_not_logged_in(self):
        response = self.client.get("/attachment/{}".format(self.attachment.id))
        self.assertEqual(response.status_code, 401)
        self.assertFalse(hasattr(response, 'streaming_content'))

    def test_attachment_not_authorized(self):
        self.client.force_login(self.user2)
        response = self.client.get("/attachment/{}".format(self.attachment.id))
        self.assertTemplateUsed(response, 'react.html')
        self.assertFalse(hasattr(response, 'streaming_content'))

    def test_attachment(self):
        self.client.force_login(self.user1)
        response = self.client.get("/attachment/{}".format(self.attachment.id))
        self.assertTemplateNotUsed(response, 'react.html')
        self.assertTrue(list(response.streaming_content), "Demo upload file.")