import os

from django.db import connection
from PIL import Image
from core.models.attachment import Attachment
from core.models.image import ResizedImage
from django_tenants.test.client import TenantClient
from tenants.helpers import FastTenantTestCase
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

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)
        cache.set("%s%s" % (connection.schema_name, 'IS_CLOSED'), False)

        self.client = TenantClient(self.tenant)

        self.blog = mixer.blend(Blog, read_access=[ACCESS_TYPE.public], owner=self.authenticatedUser)

    def tearDown(self):
        pass

    def get_image(self, filename, size=(800, 1280)):
        output = BytesIO()
        img = Image.new("RGB", size, (255, 255, 255))
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
    def test_resize_resolve(self, mock_send_task):
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

    def test_resize_square(self):
        size = 414
        attachment = mixer.blend(Attachment, upload=self.get_image('testfile.jpg', size=(1000, 1000)))
        img = ResizedImage.objects.create(
            original=attachment,
            size=size,
        )

        image_resize.s(self.tenant.schema_name, img.pk).apply()
        img = ResizedImage.objects.get(pk=img.pk)

        self.assertEqual(img.status, ResizedImage.OK)
        resized = Image.open(img.upload.open())
        self.assertEqual(resized.width, size)
        self.assertEqual(resized.height, size)

    def test_resize_small(self):
        size = 414
        height = 10
        attachment = mixer.blend(Attachment, upload=self.get_image('testfile.jpg', size=(1000, height)))
        img = ResizedImage.objects.create(
            original=attachment,
            size=size,
        )

        image_resize.s(self.tenant.schema_name, img.pk).apply()
        img = ResizedImage.objects.get(pk=img.pk)

        self.assertEqual(img.status, ResizedImage.OK)
        resized = Image.open(img.upload.open())
        self.assertEqual(resized.height, height)

    def test_resize_vertical(self):
        size = 414
        attachment = mixer.blend(Attachment, upload=self.get_image('testfile.jpg', size=(800, 1000)))
        img = ResizedImage.objects.create(
            original=attachment,
            size=size,
        )

        image_resize.s(self.tenant.schema_name, img.pk).apply()
        img = ResizedImage.objects.get(pk=img.pk)

        self.assertEqual(img.status, ResizedImage.OK)
        resized = Image.open(img.upload.open())
        self.assertEqual(resized.width, size)

    def test_resize_horizontal(self):
        size = 414
        attachment = mixer.blend(Attachment, upload=self.get_image('testfile.jpg', size=(1000, 800)))
        img = ResizedImage.objects.create(
            original=attachment,
            size=size,
        )

        image_resize.s(self.tenant.schema_name, img.pk).apply()
        img = ResizedImage.objects.get(pk=img.pk)

        self.assertEqual(img.status, ResizedImage.OK)
        resized = Image.open(img.upload.open())
        self.assertEqual(resized.height, size)
