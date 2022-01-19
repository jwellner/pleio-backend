import os
from django.db import connection
from PIL import Image
from core.models.attachment import Attachment
from core.models.image import ResizedImage
from django_tenants.test.client import TenantClient
from django_tenants.test.cases import FastTenantTestCase
from mixer.backend.django import mixer
from django.core.cache import cache
from django.contrib.auth.models import AnonymousUser
from blog.models import Blog
from user.models import User
from core.lib import ACCESS_TYPE
from io import BytesIO
from django.core.files.base import ContentFile
from core.tasks import image_resize
from unittest import mock

class ResizeImageTestCase(FastTenantTestCase):

    basepath = 'test_files/'

    def setUp(self):
        os.makedirs(self.basepath, exist_ok=True)
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)
        cache.set("%s%s" % (connection.schema_name, 'IS_CLOSED'), False)

        self.client = TenantClient(self.tenant)

        self.blog = mixer.blend(Blog, read_access=[ACCESS_TYPE.public], owner=self.authenticatedUser)

    def tearDown(self):
        os.system(f"rm -r {self.basepath}")

    def get_image(self, filename):
        output = BytesIO()
        img = Image.new("RGB", (800, 1280), (255, 255, 255))
        img.save(output, "JPEG")

        contents = output.getvalue()

        return ContentFile(contents, filename)
    
    @mock.patch('celery.current_app.send_task')    
    def test_redirect(self, mock_send_task):
        attachment = Attachment.objects.create(
            attached=self.blog,
            owner=self.authenticatedUser,
            upload=self.get_image('testfile.jpg')
        )

        response = self.client.get(attachment.url + "?size=414", follow=True)

        mock_send_task.assert_called_once()
        self.assertRedirects(response, attachment.url)

    @mock.patch('celery.current_app.send_task')
    def test_resize(self, mock_send_task):
        attachment = Attachment.objects.create(
            attached=self.blog,
            owner=self.authenticatedUser,
            upload=self.get_image('testfile.jpg')
        )
        ResizedImage.objects.create(
            original=attachment,
            size=414,
            upload=self.get_image('testfile2.jpg'),
            status='OK'
        )

        response = self.client.get(attachment.url + "?size=414")

        mock_send_task.assert_not_called()

        self.assertEqual(response.status_code, 200)