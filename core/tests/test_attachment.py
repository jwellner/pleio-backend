import uuid

from django.urls import reverse

from core.tests.helpers import PleioTenantTestCase
from core.models import Attachment
from mixer.backend.django import mixer
from user.factories import UserFactory


class AttachmentTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.user1 = UserFactory(email="user1@example.net")
        self.user2 = UserFactory(email="user2@example.net")
        self.attachment = mixer.blend(Attachment,
            upload=self.build_contentfile(self.relative_path(__file__, ['assets', 'exif_example.jpg'])),
            owner = self.user1)

    def test_attachment_not_authorized(self):
        self.client.force_login(self.user2)

        response = self.client.get(reverse("attachment", args=[self.attachment.id]))

        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'react.html')

    def test_attachment(self):
        self.client.force_login(self.user1)

        response = self.client.get(reverse("attachment", args=[self.attachment.id]))
        content = response.getvalue()

        self.assertEqual(response.status_code, 200)
        self.assertTemplateNotUsed(response, 'react.html')
        self.assertEqual(content, self.attachment.upload.open().read())

    def test_fetch_non_existing_attachment(self):
        some_id = uuid.uuid4()
        self.client.force_login(self.user1)

        response = self.client.get(reverse("attachment", args=[some_id]))

        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed("react.html")
